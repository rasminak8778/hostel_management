# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class HostelFacilities(models.Model):
    """add room facilities"""
    _name = 'hostel.facilities'
    _description = 'Hostel Facilities'

    name = fields.Char(string='Name',  required=True,)
    charge = fields.Integer(string='Charge')

    @api.constrains('charge')
    def _check_charge(self):
        """function defined for charge !=0"""
        if self.charge <= 0:
            raise (ValidationError("Please Provide the Charge greater than 0"))
