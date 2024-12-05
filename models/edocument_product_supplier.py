# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ElectronicDocumentProductSupplierinfo(models.Model):
    _description = "Lista de productos Homologados"
    _name = "edocument.product.supplier"

    _order = 'sequence, id'
    _rec_name = 'partner_id'

    def _default_product_id(self):
        product_id = self.env.get('default_product_id')
        if not product_id:
            model, active_id = [self.env.context.get(k) for k in ['model', 'active_id']]
            if model == 'product.product' and active_id:
                product_id = self.env[model].browse(active_id).exists()
        return product_id

    partner_id = fields.Many2one(
        'res.partner', 'Proveedor',
        ondelete='cascade', required=True,
        check_company=True)
    product_name = fields.Char(
        'Nombre de Producto')
    product_code = fields.Char(
        'Codigo de Producto')
    sequence = fields.Integer(
        'Sequencia', default=1)
    product_uom = fields.Many2one(
        'uom.uom', 'Unidad de Medida')
    company_id = fields.Many2one(
        'res.company', 'Compania',
        default=lambda self: self.env.company.id, index=1)
    product_id = fields.Many2one(
        'product.product', 'Producto Variante', check_company=True,
        ondelete='cascade',
        domain="[('product_tmpl_id', '=', product_tmpl_id)] if product_tmpl_id else []",
        default=_default_product_id)
    product_tmpl_id = fields.Many2one(
        'product.template', 'Producto Template', check_company=True,
        index=True, ondelete='cascade')
    product_variant_count = fields.Integer('Variant Count', related='product_tmpl_id.product_variant_count')

    unificar = fields.Boolean(default=False)
    distribuir = fields.Boolean(default=False)
    distribuir_code = fields.Char('Codigo producto para Distribución')

    uom_ids_allowed = fields.Many2many('uom.uom', compute='_compute_uom_ids_allowed', string='UdM Permitidos')

    # @api.onchange('product_id','product_tmpl_id')
    # def _compute_uom_ids_allowed(self):
    #     for line in self:
    #         if line.product_id:
    #             uom_records = line.product_id.purchase_uom_ids
    #             if line.product_id.uom_po_id not in uom_records:
    #                 uom_records |= line.product_id.uom_po_id
    #             line.uom_ids_allowed = uom_records


    @api.depends('product_tmpl_id')
    def _compute_uom_ids_allowed(self):
        for line in self:
            if line.product_tmpl_id:
                uom_records = line.product_tmpl_id.sale_uom_ids
                if line.product_tmpl_id.uom_id not in uom_records:
                    uom_records |= line.product_tmpl_id.uom_id
                line.uom_ids_allowed = uom_records
            else:
                line.uom_ids_allowed = self.env['uom.uom']

    @api.onchange('product_tmpl_id')
    def _compute_uom_ids_allowed_onchange(self):
        self._compute_uom_ids_allowed()


    _sql_constraints = [
        ('unique_supplier_product_code',
         'unique(partner_id, product_tmpl_id, product_code)',
         'Ya existe un registro con el mismo proveedor, producto y código.'),
    ]


    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        """Clear product variant if it no longer matches the product template."""
        if self.product_id and self.product_id not in self.product_tmpl_id.product_variant_ids:
            self.product_id = False

    def _sanitize_vals(self, vals):
        """Sanitize vals to sync product variant & template on read/write."""
        # add product's product_tmpl_id if none present in vals
        if  vals.get('product_id') and not vals.get('product_tmpl_id'):
            product = self.env['product.product'].browse(vals['product_id'])
            vals['product_tmpl_id'] = product.product_tmpl_id.id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sanitize_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._sanitize_vals(vals)
        return super().write(vals)
