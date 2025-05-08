from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LaserMassCutWizard(models.TransientModel):
    _name = "laser.mass.cut.wizard"
    _description = "Wizard to process MRP Orders for Laser Mass Cut"

    steel_piece_order_ids = fields.Many2many(
        "mrp.production", string="Orders with Steel Piece", readonly=True
    )

    steel_piece_total_qty = fields.Integer(
        string="Number of Steel Piece Components",
        compute="_compute_steel_piece_total_qty",
    )

    produce_offcut = fields.Boolean(string="Produce Steel Sheet Offcut")

    show_material_selection = fields.Boolean(compute="_compute_show_material_selection")

    selected_material_product_id = fields.Many2one(
        "product.product",
        string="Material to Use",
        domain=lambda self: [
            (
                "id",
                "in",
                [
                    self.env.ref("laser_mass_cut.product_steel_sheet").id,
                    self.env.ref("laser_mass_cut.product_steel_sheet_offcut").id,
                ],
            )
        ],
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get("default_mrp_order_ids")
        steel_piece = self.env.ref("laser_mass_cut.product_steel_piece")
        if active_ids and steel_piece:
            selected_orders = self.env["mrp.production"].browse(active_ids)

            # prüfe auf ungültige Aufträge
            invalid_orders = selected_orders.filtered(
                lambda o: o.state != "confirmed"
                or steel_piece.id not in o.move_raw_ids.mapped("product_id").ids
            )
            if invalid_orders:
                invalid_names = ", ".join(invalid_orders.mapped("name"))
                raise UserError(
                    _(
                        "The following orders are invalid (not confirmed or missing "
                        f"Steel Piece as component): {invalid_names}"
                    )
                )

            res["steel_piece_order_ids"] = [(6, 0, selected_orders.ids)]
        return res

    @api.depends("steel_piece_order_ids")
    def _compute_steel_piece_total_qty(self):
        steel_piece = self.env.ref("laser_mass_cut.product_steel_piece")
        for wizard in self:
            total_qty = sum(
                move.product_uom_qty
                for order in wizard.steel_piece_order_ids
                for move in order.move_raw_ids
                if move.product_id == steel_piece
            )
            wizard.steel_piece_total_qty = total_qty

    @api.depends("selected_material_product_id")
    def _compute_show_material_selection(self):
        product_offcut = self.env.ref("laser_mass_cut.product_steel_sheet_offcut")
        available_qty = product_offcut.virtual_available
        for wizard in self:
            if available_qty >= 1:
                wizard.show_material_selection = True
            else:
                wizard.show_material_selection = False
                wizard.selected_material_product_id = self.env.ref(
                    "laser_mass_cut.product_steel_sheet"
                )

    def process_orders(self):
        product_sheet = self.selected_material_product_id or self.env.ref(
            "laser_mass_cut.product_steel_sheet"
        )
        product_piece = self.env.ref("laser_mass_cut.product_steel_piece")

        production = self.env["mrp.production"].create(
            {
                "product_id": product_piece.id,
                "product_qty": self.steel_piece_total_qty,
                "product_uom_id": product_piece.uom_id.id,
            }
        )

        self.env["stock.move"].create(
            {
                "product_id": product_sheet.id,
                "product_uom_qty": 1.0,
                "product_uom": product_sheet.uom_id.id,
                "location_id": production.location_src_id.id,
                "location_dest_id": production.location_dest_id.id,
                "raw_material_production_id": production.id,
                "name": product_sheet.display_name,
            }
        )

        if self.produce_offcut:
            product_offcut = self.env.ref("laser_mass_cut.product_steel_sheet_offcut")
            self.env["stock.move"].create(
                {
                    "product_id": product_offcut.id,
                    "product_uom_qty": 1.0,
                    "product_uom": product_offcut.uom_id.id,
                    "location_id": production.location_dest_id.id,
                    "location_dest_id": production.location_dest_id.id,
                    "production_id": production.id,
                    "name": product_offcut.display_name,
                }
            )

        production.action_confirm()
        production.button_mark_done()

        # Mark all steel_piece_order_ids as done
        for order in self.steel_piece_order_ids:
            if order.state not in ("done", "cancel"):
                order.button_mark_done()

        production.message_post(
            body=f"Production order confirmed for {self.steel_piece_total_qty} Steel "
            f"Pieces using {product_sheet.display_name}"
            + (" and creating 1 Offcut." if self.produce_offcut else ".")
        )

        return {"type": "ir.actions.act_window_close"}
