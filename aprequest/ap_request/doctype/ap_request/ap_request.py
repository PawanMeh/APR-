# -*- coding: utf-8 -*-
# Copyright (c) 2020, hello@openetech.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from aprequest.custom_method import make_sap_feed, split_apr

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
							name != %s
						''', (self.invoice_date, self.invoice_ref, self.name))
		if inv_refs:
			frappe.throw(_("Duplicate invoice exists for {0}".format("<a href='desk#Form/AP Request/{0}'> AP Request {0} </a>".format(inv_refs[0][0]))))

		if self.closure_type in ["PO Invoice", "Non PO Invoice"] and not self.final_invoice_copy:
			frappe.throw(_("Final Invoice copy is mandatory if closure is by PO Invoice or Non PO Invoice"))

		if self.closure_type == "Non PO Invoice" and not self.final_approval_copy:
			frappe.throw(_("Final Invoice copy is mandatory if closure is by PO Invoice or Non PO Invoice"))

		if self.closure_type == "Split" and self.no_of_split < 1:
			frappe.throw(_("Enter no of APRs to be created via Split"))

	def on_update(self):
		pass
	def on_submit(self):
		#validate mandatory answers
		if self.closure_type:
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
		else:
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