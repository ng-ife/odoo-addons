import subprocess
import os

from odoo import api, fields, models


class RepoBranch(models.Model):
    _name = "ife.repo.branch"
    _description = "Repository Branch"

    name = fields.Char(string="Branch Name", required=True)
    repo_id = fields.Many2one("ife.repo", string="Repository", required=True)
    full_path = fields.Char(related="repo_id.full_path")
    is_cloned = fields.Boolean(string="Is Cloned", related="repo_id.is_cloned")
    is_dirty = fields.Boolean(related="repo_id.is_dirty")

    def checkout(self):
        self.ensure_one()
        if not self.is_cloned:
            raise models.ValidationError("Repo is not cloned yet.")
        try:
            path = self.full_path
            subprocess.run(
                ["git", "-C", path, "checkout", self.name],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or str(e)
            raise models.ValidationError(f"Git checkout failed: {error_msg}")
        return True
    
    def action_clean(self):
        self.ensure_one()
        if not self.is_cloned:
            raise models.ValidationError("Repo is not cloned yet.")
        try:
            path = self.full_path
            result = subprocess.run(
                ["git", "-C", path, "rev-parse", "--abbrev-ref", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
            current_branch = result.stdout.strip()
            if current_branch != self.name:
                raise models.ValidationError(f"Not on branch '{self.name}'. Current branch: '{current_branch}'")
            self.repo_id.action_clean()
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or str(e)
            raise models.ValidationError(f"Git clean failed: {error_msg}")
        return True

    def action_pull_branch(self):
        self.ensure_one()
        self.checkout()
        try:
            path = self.full_path
            subprocess.run(
                ["git", "-C", path, "pull", "origin", self.name],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or str(e)
            raise models.ValidationError(f"Git pull failed: {error_msg}")
        return True

    def action_commit_and_push_branch(self):
        self.ensure_one()
        self.checkout()
        if not self.is_dirty:
            raise models.ValidationError("No changes to commit and push.")
        try:
            path = self.full_path
            subprocess.run(
                ["git", "-C", path, "add", "."],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "-C", path, "commit", "-m", "Commit from Odoo"],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "-C", path, "push", "origin", self.name],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or str(e)
            raise models.ValidationError(f"Git commit/push failed: {error_msg}")
        return True
    
    def read_file(self, file_path):
        self.ensure_one()
        self.checkout()
        full_file_path = os.path.join(self.full_path, file_path)
        try:
            with open(full_file_path, "r") as f:
                content = f.read()
        except Exception as e:
            raise models.ValidationError(f"Failed to read file: {str(e)}")
        return content
    
    def write_file(self, file_path, content):
        self.ensure_one()
        self.checkout()
        full_file_path = os.path.join(self.full_path, file_path)
        try:
            with open(full_file_path, "w") as f:
                f.write(content)
        except Exception as e:
            raise models.ValidationError(f"Failed to write file: {str(e)}")
        return True
