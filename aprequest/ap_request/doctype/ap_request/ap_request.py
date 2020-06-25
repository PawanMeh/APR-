# -*- coding: utf-8 -*-
# Copyright (c) 2020, hello@openetech.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

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
	def on_update(self):
		pass
	def on_submit(self):
		pass
	def on_cancel(self):
		pass