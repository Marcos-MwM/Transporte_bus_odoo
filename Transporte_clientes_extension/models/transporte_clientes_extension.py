from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TransporteClienteExtension(models.Model):
    _inherit = "transporte.publico"

    # ── Ruta ──────────────────────────────────────────────────────────────────
    ruta_id = fields.Many2one(
        'transporte.ruta',
        string='Ruta de Transporte',
        required=True
    )

    origen = fields.Char(
        string="Origen",
        related="ruta_id.origen",
        readonly=True
    )
    destino = fields.Char(
        string="Destino",
        related="ruta_id.destino",
        readonly=True
    )
    pasaje = fields.Float(
        string="Pasaje",
        related="ruta_id.pasaje",
        readonly=True
    )
    imagen_de_referencia = fields.Image(
        string="Imagen de referencia del Autobus",
        related="ruta_id.imagen_de_referencia",
        readonly=True
    )

    # ── Descuentos y precio ──────────────
    total_de_descuento = fields.Float(
        string="Descuento (%)",
        compute="_compute_descuento",
        store=True
    )
    precio_final = fields.Float(
        string="Precio Final",
        compute="_compute_tarifa_final",
        store=True,
        readonly=True
    )

    # ── Pago─────────────────────────────────────────────────────────
    metodo_pago = fields.Selection(
        selection=[
            ('efectivo',      'Efectivo'),
            ('tarjeta',       'Tarjeta'),
            ('transferencia', 'Transferencia'),
            ('qr',            'Código QR'),
        ],
        string="Método de Pago"
    )

    estado_pago = fields.Selection(
        selection=[
            ('pendiente',   'Pendiente'),
            ('pagado',      'Pagado'),
            ('reembolsado', 'Reembolsado'),
        ],
        string="Estado de Pago",
        default='pendiente'
    )
    fecha_pago = fields.Datetime(
        string="Fecha de Pago",
        required=True
    )
    numero_comprobante = fields.Char(
        string="Número de Comprobante",
        required=True
    )

    def action_pagado(self):
        for record in self:
            record.estado_pago = 'pagado'

    def action_pendiente(self):
        for record in self:
            record.estado_pago = 'pendiente'

    def action_reembolsado(self):
        for record in self:
            record.estado_pago = 'reembolsado'
    # ── Compute ────────────────────────────────────────────
    @api.depends('discapacidad', 'estudiante', 'edad')
    def _compute_descuento(self):
        for r in self:
            if r.discapacidad:
                r.total_de_descuento = 75
            elif r.estudiante:
                r.total_de_descuento = 50
            elif r.edad <= 17:
                r.total_de_descuento = 50
            elif r.edad >= 65:
                r.total_de_descuento = 40
            else:
                r.total_de_descuento = 0

    @api.depends('pasaje', 'total_de_descuento')
    def _compute_tarifa_final(self):
        for registro in self:
            registro.precio_final = registro.pasaje * (1 - registro.total_de_descuento / 100)

    # ── Onchange ──────────────────────────────────────────────────────────────
    @api.onchange('estado_pago')
    def _onchange_estado_pago(self):
        if self.estado_pago == 'pagado':
            self.fecha_pago = fields.Datetime.now()

    # ── Validaciones ────────────────────────────────────────────────────────────
    @api.constrains('fecha_pago', 'estado_pago')
    def _check_fecha_pago(self):
        for registro in self:
            if (
                registro.estado_pago == 'pendiente'
                and registro.fecha_pago
                and registro.fecha_pago < fields.Datetime.now()
            ):
                raise ValidationError(
                    "Un pago pendiente no puede tener fecha en el pasado."
                )


