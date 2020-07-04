# -*- coding: utf-8 -*-
# Copyright (c) 2020, hello@openetech.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class SAPFeed(Document):
	def validate(self):
		if not self.apr:
			frappe.throw(_("SAP Feed cannot be created without reference to APR"))
		if ((self.sapf_status == "Prepared" or self.docstatus == 1) and (not self.posting_date or not self.accounting_doc)):
			frappe.throw(_("Posting Date and Accounting Date are required."))

	def on_submit(self):
		apr_doc = frappe.get_doc('AP Request', self.apr)
		apr_doc.posting_date = self.posting_date
		apr_doc.accounting_doc = self.accounting_doc
		apr_doc.sapf_status = "Reviewed"
		apr_doc.save()
