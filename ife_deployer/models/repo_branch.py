from odoo import models, fields, api
import os
import subprocess

class RepoBranch(models.Model):
    _name = 'ife.repo.branch'
    _description = 'Repository Branch'

    name = fields.Char(string='Branch Name', required=True)
    repo_id = fields.Many2one('ife.repo', string='Repository', required=True)
    full_path = fields.Char(related='repo_id.full_path')
    is_cloned = fields.Boolean(string='Is Cloned', related='repo_id.is_cloned')
    is_dirty = fields.Boolean(string='Is Dirty', compute='_compute_is_dirty')

    @api.depends('repo_id', 'name')
    def _compute_is_dirty(self):
        for rec in self:
            if rec.is_cloned:
                try:
                    path = rec.full_path
                    result = subprocess.run(
                        ['git', '-C', path, 'status', '--porcelain'],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    rec.is_dirty = bool(result.stdout.strip())
                except Exception:
                    rec.is_dirty = False
            else:
                rec.is_dirty = False
                
    def checkout(self):
        self.ensure_one()
        if not self.is_cloned:
            raise models.ValidationError("Repo is not cloned yet.")
        try:
            path = self.full_path
            subprocess.run(
                ['git', '-C', path, 'checkout', self.name],
                check=True,
                capture_output=True,
                text=True
                )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or str(e)
            raise models.ValidationError(f"Git checkout failed: {error_msg}")
        return True

    def action_pull_branch(self):
        self.ensure_one()
        if not self.is_cloned:
            raise models.ValidationError("Repo is not cloned yet.")
        try:
            path = self.full_path
            subprocess.run(
                    ['git', '-C', path, 'pull', 'origin', self.name],
                    check=True,
                    capture_output=True,
                    text=True
                )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or str(e)
            raise models.ValidationError(f"Git pull failed: {error_msg}")
        return True

    def action_commit_and_push_branch(self):
        self.ensure_one()
        if not self.is_cloned:
            raise models.ValidationError("Repo is not cloned yet.")
        if not self.is_dirty:
            raise models.ValidationError("No changes to commit and push.")
        try:
            path = self.full_path
            subprocess.run(
                    ['git', '-C', path, 'add', '.'],
                    check=True,
                    capture_output=True,
                    text=True
            )
            subprocess.run(
                ['git', '-C', path, 'commit', '-m', 'Commit from Odoo'],
                check=True,
                capture_output=True,
                text=True
            )
            subprocess.run(
                ['git', '-C', path, 'push', 'origin', rec.name],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or str(e)
            raise models.ValidationError(f"Git commit/push failed: {error_msg}")
        return True
