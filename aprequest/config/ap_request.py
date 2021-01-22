# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	data = [
		{	
			"module_name": "AP Request",
			"label": _("Set Up"),
			"items": [
				{
					"type": "doctype",
					"name": "Transaction Type",
					"description": _("Transaction Type")
				},
				{
					"type": "doctype",
					"name": "Question",
					"description": _("Question")
				}
			]
		},
		{	
			"module_name": "Support",
			"label": _("AP Issue Inbox"),
			"items": [
				{
					"type": "doctype",
					"name": "Issue",
					"description": _("AP Issue")
				},
				{
					"type": "doctype",
					"name": "Query",
					"description": _("AP Query")
				}
			]
		},
		{	
			"module_name": "AP Request",
			"label": _("Transaction"),
			"items": [
				{
					"type": "doctype",
					"name": "AP Request",
					"description": _("AP Request")
				},
				{
					"type": "doctype",
					"name": "SAP Feed",
					"description": _("SAP Feed")
				},
				{
					"type": "doctype",
					"name": "GR Request",
					"description": _("GR Request")
				}
			]
		},
		{	
			"module_name": "AP Request",
			"label": _("Time Tracking"),
			"items": [
				{
					"type": "doctype",
					"name": "Time Tracker",
					"description": _("AP Request")
				}
			]
		}
	]

	return data