# -*- coding: utf-8 -*-
# Copyright (c) 2020, hello@openetech.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from aprequest.custom_method import make_sap_feed, split_apr
from frappe.utils import cint, flt, add_months, today, date_diff, getdate, add_days, cstr, time_diff_in_hours

class APRequest(Document):
	def validate(self):
		def default_questions():
			table = "question"
			rev_question_detail = list(frappe.db.sql("""
									select 
										question
									from 
										`tabQuestion Detail`
									where parent = %s""", "APR", as_dict=1))
			self.set(table, [])
			for d in rev_question_detail:
				self.append(table, d)
			for d in self.question:
				d.response = "No"
		if self.get("__islocal") == 1 and not self.question:
			default_questions()
		else:
			if self.question:
				pass
			else:
				default_questions()
		#validate invoices
		inv_refs = frappe.db.sql('''
						select
							name
						from
							`tabAP Request`
						where
							invoice_date = %s and
							invoice_ref = %s and
							name != %s and
							closure_type != 'Split'
						''', (self.invoice_date, self.invoice_ref, self.name))
		if inv_refs:
			frappe.throw(_("Duplicate invoice exists for {0}".format("<a href='desk#Form/AP Request/{0}'> AP Request {0} </a>".format(inv_refs[0][0]))))

		if not (self.parent_apr or self.parent_issue):
			frappe.throw(_("Cannot create APR without reference to Issue or parent APR"))

		if self.closure_type in ["PO Invoice", "Non PO Invoice"] and not self.final_invoice_copy:
			frappe.throw(_("Final Invoice copy is mandatory if closure is by PO Invoice or Non PO Invoice"))

		if self.closure_type == "Non PO Invoice" and not self.final_approval_copy:
			frappe.throw(_("Final Approval copy is mandatory if closure is by Non PO Invoice"))

		if self.closure_type == "Split" and self.no_of_split < 1:
			frappe.throw(_("Enter no of APRs to be created via Split"))
		elif self.closure_type in ["PO Invoice", "Non PO Invoice"] and self.no_of_split > 1:
			frappe.throw(_("No of splits should be zero for closure type of PO and Non PO Invoice"))

		if self.closure_type == "Split" and (self.sap_po_number or self.company_code_sap
			or self.final_invoice_copy or self.final_approval_copy or
			self.eb_npi_approver or self.eb_npi_email or self.eb_npi_approval_obtained):
			frappe.throw(_("There should be no values in SAP PO Number/SAP Company Code/Final Invoice Copy/Final Approval Copy/EB NPI Approver/EB NPI Email/EB NPI Obtained for Closure Type of split"))
		elif self.closure_type == "PO Invoice" and (self.final_approval_copy or
			self.eb_npi_approver or self.eb_npi_email or self.eb_npi_approval_obtained):
			frappe.throw("There should be no values in Final Approval Copy/EB NPI Approver/EP NPI Email/EB NPI Obtained for Closure Type of PO Invoice")
		elif self.closure_type == "PO Invoice" and (not self.sap_po_number or not self.company_code_sap
			or not self.sapf_assigned_to or not self.final_invoice_copy):
			frappe.throw(_("SAP PO Number/SAP Company Code/SAPF Assigned To/Final Invoice Copy is mandatory for PO Invoice"))
		elif self.closure_type == "PO Invoice":
			for d in self.invoice_line:
				if (not d.po_line_ref or not d.po_line_amt or not d.po_line_qty or not d.inv_line_amt or not d.inv_line_qty):
					frappe.throw(_("Please enter PO line details"))
		elif self.closure_type == "Non PO Invoice" and (self.sap_po_number):
			frappe.throw(_("SAP PO Number should be blank for Non PO Invoice"))
		elif self.closure_type == "Non PO Invoice" and (not self.company_code_sap
			or not self.sapf_assigned_to or not self.final_invoice_copy or not self.final_approval_copy or
			not self.eb_npi_approver or not self.eb_npi_email or not self.eb_npi_approval_obtained):
			frappe.throw(_("SAP Company Code/SAPF Assigned To/Final Invoice Copy/Final Approval Copy/EB NPI Approver/EB NPI Email/EB NPI Obtained is mandatory for Non PO Invoice"))

		if date_diff(self.invoice_date, today()) > 0:
			frappe.throw(_("Invoice date cannot be greater than current date"))
		#calc
		planned_cost = 0
		bal_amt = 0
		if self.closure_type in ["PO Invoice", "Non PO Invoice"]:
			if self.invoice_line:
				for d in self.invoice_line:
					if self.closure_type == "PO Invoice" and (not d.po_line_ref or not d.po_line_amt > 0 or not d.po_line_qty > 0 or not d.inv_line_qty > 0 or not d.inv_line_amt > 0):
						frappe.throw(_("Please enter PO Line Ref/PO Line Amount/PO Line Quantity/Invoice Line Quantity/Invoice Line Amount in Invoice Line table values for PO Invoice"))
					if self.closure_type == "Non PO Invoice" and (not d.inv_line_amt > 0 or not d.gl_account or not d.cost_center or not d.tax_code):
						frappe.throw(_("Please enter Invoice Line Amount/GL Account/Cost Center/Tax Code in Invoice Line table for Non PO Invoice"))
					planned_cost += d.inv_line_amt
			else:
				frappe.throw(_("Please enter all values in invoice line table"))
		else:
			for d in self.invoice_line:
				planned_cost += d.inv_line_amt

		self.planned_cost = planned_cost
		self.balance_amt = self.invoice_amount - self.planned_cost - self.unplanned_cost
		frappe.msgprint("Balance Amount {0} invoice amount {1} planned - cost {2} unplanned - cost {3}".format(self.balance_amt, self.invoice_amount, self.planned_cost, self.unplanned_cost))
		if self.closure_type == "Split" and (self.balance_amt != self.invoice_amount):
			frappe.throw(_("Balance Amount should be equal to invoice amount"))
		elif ((self.closure_type in ["PO Invoice", "Non PO Invoice"]) and (self.balance_amt != 0)):
			frappe.throw(_("Balance Amount should be zero for PO and Non PO Invoice. Check invoice amounts and PO line amounts."))

	def on_update(self):
		self.balance_amt = flt(self.invoice_amount) - flt(self.planned_cost) - flt(self.unplanned_cost)

	def on_submit(self):
		#validate mandatory answers
		if self.closure_type and self.closure_type != "Short Close":
			question = frappe.db.sql('''
							select
								enforce_mandatory
							from
								`tabQuestion`
							where
								type = 'APR'
						''', as_list=1)
			if question[0][0]:
				for d in self.question:
					if d.response == "No":
						frappe.throw(_("Questionnaire repsonse should be either NA or Yes"))

		if not self.closure_type:
			frappe.throw(_("Closure Type is mandatory"))

		related_aprs = frappe.db.sql('''
						select
							name
						from
							`tabAP Request`
						where
							docstatus = 0 and
							parent_apr = %s
						''', self.name, as_list=1)

		if related_aprs:
			frappe.throw(_("All related APRs should be closed before final approval of current APR"))

		related_issues =  frappe.db.sql('''
								select
									name
								from
									`tabIssue`
								where
									apr = %s and status != 'Closed'
								''', self.name, as_list=1)

		if related_issues:
			frappe.throw(_("All related Issues should be closed before final approval of current APR"))

		if self.closure_type in ["PO Invoice", "Non PO Invoice"]:
			make_sap_feed(self.name)
		elif self.closure_type == "Split":
			split_apr(self.name)

	def on_cancel(self):
		pass