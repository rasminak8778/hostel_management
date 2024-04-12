# -*- coding: utf-8 -*-
from odoo import fields, models, api


class LeaveRequest(models.Model):
    """contains the leave request details"""
    _name = 'leave.request'
    _description = 'Leave Request'
    _rec_name = 'student_name_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    student_name_id = fields.Many2one('student.information',
                                      string='Student Name')
    leave_date = fields.Date(string='Leave Date',  required=True)
    arrival_date = fields.Date(string='Arrival Date')
    status = fields.Selection(selection=[('new', 'New'),
                                         ('approved', 'Approved')],
                              default='new', tracking=True)
    room_id = fields.Many2one('room.management', copy=False,
                                 related='student_name_id.room_id', store=True)
    duration = fields.Float(string='Duration', compute='_compute_duration', store=True)
    def create_cleaning_request(self):
        """function defined for create cleaning request"""
        self.env['cleaning.service'].create({
                        'room_id':  self.student_name_id.room_id.id

        })

    @api.depends('leave_date','arrival_date')
    def _compute_duration(self):
        for record in self:
            if record.leave_date and record.arrival_date:
               duration = (record.arrival_date - record.leave_date).days
               record.duration = duration
            else:
                record.duration = 0
    def action_approve(self):
        """function defined for action approve"""
        self.status = 'approved'
        if self.student_name_id.room_id.std_count >= 1:
            self.create_cleaning_request()
