# -*- coding: utf-8 -*-
from odoo import fields, models


class CleaningService(models.Model):
    """manage cleaning services"""
    _name = 'cleaning.service'
    _description = 'Cleaning Service'
    _rec_name = 'room_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    room_id = fields.Many2one('room.management', string='Room',
                              required=True, tracking=True
                              )
    start_time = fields.Date(string='Start Time',
                             help='Provide the starting '
                                  'time of the cleaning work')
    cleaning_staff_id = fields.Many2one('res.users',
                                        string='Cleaning Staff'
                                        )
    state = fields.Selection(selection=[('new', 'New'), ('assigned',
                                                         'Assigned'), ('done',
                                                                       'Done')],
                             tracking=True)
    company_id = fields.Many2one('res.company', copy=False,
                                 default=lambda self: self.env.user.company_id.
                                 id)

    def action_assign(self):
        """function for button assign"""
        self.write({
            'state': "assigned"
        })
        self.write({'cleaning_staff_id': self.env.user.id})
        # print(self.env.user)

    def action_complete(self):
        """function for button complete"""
        self.write({
            'state': "done"
        })
