{
    "name": "Steel Sheet Configurator",
    "summary": "Laser Cutter Sheet Configuration Module",
    "author": "Niels Göttsch",
    "website": "https://www.ife.de",
    "category": "Manufacturing",
    "version": "18.0.1.0.0",
    "depends": ["mrp", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/configuration.xml",
        "data/product_data.xml",
        "views/laser_mass_cut_action.xml",
        "wizard/laser_mass_cut_views.xml",
    ],
    "license": "LGPL-3",
    "application": True,
}
