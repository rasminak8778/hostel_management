# -*- coding: utf-8 -*-
from odoo import models


class StudentReport(models.AbstractModel):
    _name = 'report.hostel_management.report_leave'

    def _get_report_values(self, docids, data=None):
        print('data leave', data)
        return {'doc_ids': docids,
                'doc_model': 'leave.request',
                'data': data,
                }
