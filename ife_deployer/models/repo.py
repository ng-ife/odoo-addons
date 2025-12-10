import os
import subprocess

from odoo import api, fields, models

REPO_CLONE_BASE_PATH = "/home/niels/tmp/ife-deployer-repos"

REPO_TYPE = [("project", "Project"), ("config", "Config"), ("module", "Module")]


class Repo(models.Model):
    _name = "ife.repo"
    _description = "Repository"

    name = fields.Char(required=True)
    path = fields.Char(string="Local Path", required=True)
    full_path = fields.Char(string="Absolute Path", compute="_compute_clone_path")
    github_url = fields.Char(string="GitHub URL", required=True)
    type = fields.Selection(REPO_TYPE, string="Type", required=True)
    is_cloned = fields.Boolean(string="Is Cloned", compute="_compute_is_cloned")
    is_dirty = fields.Boolean(string="Is Dirty", compute="_compute_is_dirty")
    branch_count = fields.Integer(
        string="Branch Count", compute="_compute_branch_count"
    )
    branch_ids = fields.One2many("ife.repo.branch", "repo_id", string="Branches")

    _sql_constraints = [
        (
            "unique_path",
            "unique(path)",
            "The local path for a repository must be unique!",
        ),
    ]

    @api.constrains("path")
    def _check_path_validity(self):
        for rec in self:
            if not rec.path:
                raise models.ValidationError("Repository path must not be empty!")
            if os.path.isabs(rec.path):
                raise models.ValidationError(
                    "Repository path must be relative, not absolute!"
                )
            if "." in rec.path:
                raise models.ValidationError("Repository path must not contain dots!")
            if any(c.isspace() for c in rec.path):
                raise models.ValidationError(
                    "Repository path must not contain whitespaces!"
                )

    @api.depends("path")
    def _compute_clone_path(self):
        for rec in self:
            rec.full_path = os.path.join(REPO_CLONE_BASE_PATH, rec.path)

    @api.depends("path")
    def _compute_is_cloned(self):
        for rec in self:
            path = rec.full_path
            rec.is_cloned = os.path.isdir(os.path.join(path, ".git"))
            
    @api.depends("path")
    def _compute_is_dirty(self):
        for rec in self:
            if rec.is_cloned:
                try:
                    path = rec.full_path
                    result = subprocess.run(
                        ["git", "-C", path, "status", "--porcelain"],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    rec.is_dirty = bool(result.stdout.strip())
                except Exception:
                    rec.is_dirty = False
            else:
                rec.is_dirty = False

    def _compute_branch_count(self):
        for rec in self:
            rec.branch_count = self.env["ife.repo.branch"].search_count(
                [("repo_id", "=", rec.id)]
            )

    def action_clone_repo(self):
        for rec in self:
            path = rec.full_path
            if not os.path.isdir(path):
                try:
                    subprocess.run(
                        ["git", "clone", rec.github_url, path],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                except subprocess.CalledProcessError as e:
                    error_msg = e.stderr or str(e)
                    raise models.ValidationError(f"Git clone failed: {error_msg}")
        return True
    
    def action_clean(self):
        for rec in self:
            if not rec.is_cloned:
                raise models.ValidationError("Repo is not cloned yet.")
            try:
                path = rec.full_path
                subprocess.run(
                    ["git", "-C", path, "reset", "--hard"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    ["git", "-C", path, "clean", "-fd"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr or str(e)
                raise models.ValidationError(f"Git clean/reset failed: {error_msg}")
        return True

    def action_open_branches(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Repository Branches",
            "res_model": "ife.repo.branch",
            "view_mode": "list,form",
            "domain": [("repo_id", "=", self.id)],
            "context": {"default_repo_id": self.id},
        }
