from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, add_months, today, date_diff, getdate, add_days, cstr, time_diff_in_hours
from frappe import _
import re

@frappe.whitelist()
def split_apr(docname):
	apr_doc = frappe.get_doc('AP Request', docname)
	split_no = apr_doc.no_of_split
	if split_no > 0:
		child_req = ''
		for x in range(split_no):
			ap_doc = frappe.new_doc('AP Request')
			ap_doc.apr_date =  today()
			ap_doc.apr_status = 'Initiated'
			ap_doc.supplier = apr_doc.supplier
			ap_doc.parent_apr = apr_doc.name
			ap_doc.insert(ignore_mandatory=True, ignore_permissions=True)
			child_req += ap_doc.name + '/'

		apr_doc.child_apr = child_req
		apr_doc.save()
		apr_doc.submit()
		if apr_doc.name:
			frappe.msgprint("APR is split")

@frappe.whitelist()
def make_apr(docname):
	issue_doc = frappe.get_doc('Issue', docname)
	apr_doc = frappe.new_doc('AP Request')
	apr_doc.apr_date =  today()
	apr_doc.apr_status = 'Initiated'
	apr_doc.apr_assigned_to = issue_doc.apr_assigned_to
	apr_doc.supplier = issue_doc.supplier	
	apr_doc.parent_issue = issue_doc.name
	apr_doc.insert(ignore_mandatory=True, ignore_permissions=True)
	if not issue_doc.apr:
		issue_doc.apr = apr_doc.name
		issue_doc.save()
	if apr_doc.name:
		cpy_attachments('Issue', docname, 'AP Request', apr_doc.name)
		frappe.msgprint("APR is created")

@frappe.whitelist()
def make_sap_feed(docname):
	apr_doc = frappe.get_doc('AP Request', docname)
	sap_doc = frappe.new_doc('SAP Feed')
	sap_doc.sapf_date = today()
	sap_doc.sapf_status = "Initiated"
	sap_doc.apr = apr_doc.name
	sap_doc.apr_date = apr_doc.apr_date
	sap_doc.apr_reviewed_by = apr_doc.apr_reviewed_by
	sap_doc.company_code = apr_doc.company_code
	sap_doc.supplier = apr_doc.supplier
	sap_doc.sap_po_number = apr_doc.sap_po_number
	sap_doc.transaction_type = apr_doc.transaction_type
	sap_doc.invoice_currency = apr_doc.invoice_currency
	sap_doc.invoice_amount = apr_doc.invoice_amount
	sap_doc.invoice_date = apr_doc.invoice_date
	sap_doc.invoice_ref = apr_doc.invoice_ref
	sap_doc.insert(ignore_mandatory=True, ignore_permissions=True)
	file_url = apr_doc.final_invoice_copy or apr_doc.final_approval_copy
	if sap_doc.name:
		cpy_attachments('AP Request', apr_doc.name, 'SAP Feed', sap_doc.name,file_url)
		frappe.msgprint("SAP Feed is created")

def insert_comm_history(self, method):
	if self.apr:
		comm = frappe.db.sql('''
					select
						name
					from
						`tabCommunication History`
					where
						ap_issue = %s
					''', (self.name))
		if comm:
			pass
		else:
			comm_doc = frappe.new_doc('Communication History')
			comm_doc.ap_issue = self.name
			comm_doc.subject = self.subject
			comm_doc.status = self.status
			comm_doc.sent_to = self.raised_by
			comm_doc.parent = self.apr
			comm_doc.parenttype = "AP Request"
			comm_doc.parentfield = "conversation"
			comm_doc.insert(ignore_mandatory=True, ignore_permissions=True)

@frappe.whitelist()
def cpy_attachments(source_doctype, source_docname, target_doctype, target_docname, file_url=None):
	if file_url:
		attachments = frappe.db.sql('''
					select
						name
					from
						`tabFile`
					where
						attached_to_doctype = %s and
						attached_to_name = %s and
						file_url = %s
					''', (source_doctype, source_docname, file_url), as_dict=1)
	else:
		attachments = frappe.db.sql('''
					select
						name
					from
						`tabFile`
					where
						attached_to_doctype = %s and
						attached_to_name = %s
					''', (source_doctype, source_docname), as_dict=1)

	for attachment in attachments:
		old_doc = frappe.get_doc('File', attachment['name'])
		new_doc = frappe.copy_doc(old_doc)
		new_doc.attached_to_doctype = target_doctype
		new_doc.attached_to_name = target_docname
		new_doc.insert()