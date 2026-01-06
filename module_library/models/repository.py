import ast
import logging
import os
import shutil
import tempfile
from urllib.parse import quote_plus, urlparse, urlunparse

from git import Repo

from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class GitRepository(models.Model):
    _name = "git.repository"
    _description = "Git Repository"

    name = fields.Char(string="Bezeichnung", required=True)
    library_id = fields.Many2one("module.library", required=True, ondelete="cascade")

    git_url = fields.Char(string="Git URL", required=True)
    branch = fields.Char(default="16.0")
    git_user = fields.Char()
    access_token = fields.Char()

    module_ids = fields.One2many("module.library.module", "repository_id")

    last_scan = fields.Datetime()
    state = fields.Selection(
        [("draft", "Neu"), ("scanned", "Gescannt"), ("error", "Fehler")],
        default="draft",
    )

    def _get_authenticated_url(self):
        self.ensure_one()
        if not self.access_token:
            return self.git_url
        try:
            parsed = urlparse(self.git_url)
            encoded_token = quote_plus(self.access_token)
            if self.git_user:
                encoded_user = quote_plus(self.git_user)
                auth_part = f"{encoded_user}:{encoded_token}"
            else:
                auth_part = f"{encoded_token}"

            host_part = parsed.hostname
            if parsed.port:
                host_part = f"{host_part}:{parsed.port}"

            new_netloc = f"{auth_part}@{host_part}"
            return urlunparse(
                (
                    parsed.scheme,
                    new_netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )
        except Exception as e:
            raise UserError(f"URL Fehler: {e}") from e

    def action_scan_repository(self):
        self.ensure_one()
        temp_dir = tempfile.mkdtemp()
        clone_url = self._get_authenticated_url()

        try:
            _logger.info(f"Klonen von {self.git_url} gestartet...")
            Repo.clone_from(clone_url, temp_dir, branch=self.branch, depth=1)

            # Alte Einträge löschen
            self.module_ids.unlink()

            found_modules = []
            for root, _dirs, files in os.walk(temp_dir):
                if "__manifest__.py" in files:
                    manifest_path = os.path.join(root, "__manifest__.py")
                    technical_name = os.path.basename(root)
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            # Sicherer als eval()
                            manifest_data = ast.literal_eval(content)
                            if isinstance(manifest_data, dict):
                                found_modules.append(
                                    {
                                        "name": manifest_data.get("name", "Unbekannt"),
                                        "technical_name": technical_name,
                                        "summary": manifest_data.get("summary", ""),
                                        "version": manifest_data.get("version", ""),
                                        "author": manifest_data.get("author", ""),
                                        "repository_id": self.id,
                                    }
                                )
                    except Exception as e:
                        _logger.warning(
                            f"Konnte Manifest {technical_name} nicht lesen: {e}"
                        )
                        continue

            if found_modules:
                self.env["module.library.module"].create(found_modules)

            self.write({"state": "scanned", "last_scan": fields.Datetime.now()})

            # HIER IST DIE ÄNDERUNG:
            # Damit sich die Liste (One2many) aktualisiert, muss die View neu geladen werden.
            return {
                "type": "ir.actions.client",
                "tag": "reload",
            }

        except Exception as e:
            self.state = "error"
            _logger.error(f"Git Scan Fehler: {e}")
            raise UserError(f"Scan Fehler: {str(e)}") from e
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
