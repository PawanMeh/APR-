# -*- coding: utf-8 -*-
# Copyright (c) 2020, hello@openetech.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class SAPFeed(Document):
	def validate(self):
		if not self.apr:
			frappe.throw(_("SAP Feed cannot be created without reference to APR"))
	def on_submit(self):
		apr_doc = frappe.get_doc('AP Request', self.apr)
		apr_doc.posting_date = self.posting_date
		apr_doc.accounting_doc = self.accounting_doc
		apr_doc.save()
