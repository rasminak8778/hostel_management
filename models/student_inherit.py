# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    room_student_name = fields.Many2one('student.information',
                                        string='Student Name',
                                        help='Provide your name')

    def send_email_to_customer(self, record):
        print(self.room_student_name.id, 'wee')
        mail_template = (self.env.ref
                         ("hostel_management.invoice_email_templates"))
        mail_template.send_mail(record.id, force_send=True)

    def action_post(self):
        result = super(AccountMove, self).action_post()
        for record in self:
            self.send_email_to_customer(record)
        return result
