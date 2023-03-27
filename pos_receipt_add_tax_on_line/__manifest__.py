# Copyright 2023 - Niels Göttsch
{
    "name": "POS Add Tax to Position Line",
    "summary": "Add Tax to Position Line on POS receipt",
    "author": "Niels Göttsch",
    "company": "IFE GmbH",
    "website": "https://www.ife.de",
    "category": "Point of Sale",
    "version": "15.0.1.0.0",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "assets": {
        "web.assets_qweb": [
            "pos_receipt_add_tax_on_line/static/src/xml/OrderReceipt.xml",
        ],
    },
    "installable": True,
}
