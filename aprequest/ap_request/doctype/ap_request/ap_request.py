# -*- coding: utf-8 -*-
# Copyright (c) 2020, hello@openetech.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

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

	def on_update(self):
		pass
	def on_submit(self):
		pass
	def on_cancel(self):
		pass