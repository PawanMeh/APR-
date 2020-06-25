from __future__ import unicode_literals
import frappe
import frappe.defaults
from frappe.utils import cint, flt, add_months, today, date_diff, getdate, add_days, cstr, time_diff_in_hours
from frappe import _
from frappe.model.mapper import get_mapped_doc
from datetime import datetime
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