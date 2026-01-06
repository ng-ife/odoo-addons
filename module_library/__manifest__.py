{
    "name": "Git Module Library",
    "summary": "Verwaltung von Odoo Modulen aus Git Repositories",
    "author": "Niels Göttsch",
    "category": "Tools",
    "version": "16.0.2.0.0",
    "website": "https://www.ife.de",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/library_views.xml",
        "views/repository_views.xml",
        "views/module_views.xml",
        "views/menus.xml",
    ],
    "external_dependencies": {
        "python": ["GitPython"],
    },
    "license": "LGPL-3",
    "application": True,
}
