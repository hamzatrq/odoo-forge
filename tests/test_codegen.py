"""Tests for the code generation module (Phase 5)."""

from __future__ import annotations

import ast
import asyncio
import xml.etree.ElementTree as ET

import pytest

# ── Test fixtures ────────────────────────────────────────────────

SAMPLE_MODEL = {
    "name": "x_recipe",
    "description": "Recipe",
    "inherit": ["mail.thread"],
    "fields": [
        {"name": "name", "type": "Char", "required": True, "string": "Name"},
        {"name": "description", "type": "Text", "string": "Description"},
        {"name": "prep_time", "type": "Integer", "string": "Prep Time (min)"},
        {
            "name": "category_id",
            "type": "Many2one",
            "relation": "x_recipe.category",
            "string": "Category",
        },
        {
            "name": "stage",
            "type": "Selection",
            "selection": [["draft", "Draft"], ["active", "Active"]],
            "string": "Stage",
        },
    ],
}

SAMPLE_MODEL_SIMPLE = {
    "name": "x_tag",
    "description": "Tag",
    "fields": [
        {"name": "name", "type": "Char", "required": True, "string": "Name"},
        {"name": "color", "type": "Integer", "string": "Color Index"},
    ],
}

SAMPLE_SECURITY_GROUPS = [
    {
        "name": "recipe_user",
        "description": "Recipe User",
        "implied_group": "base.group_user",
    },
    {
        "name": "recipe_manager",
        "description": "Recipe Manager",
    },
]


# ── TestManifestGen ──────────────────────────────────────────────


class TestManifestGen:
    def test_generates_valid_python_dict(self):
        from odooforge.codegen.manifest_gen import generate_manifest

        result = generate_manifest(
            module_name="x_recipe",
            version="18.0.1.0.0",
            author="OdooForge",
            category="Customizations",
            description="Recipe Manager",
            depends=["base", "mail"],
            models=[SAMPLE_MODEL],
        )
        parsed = ast.literal_eval(result)
        assert isinstance(parsed, dict)

    def test_includes_required_keys(self):
        from odooforge.codegen.manifest_gen import generate_manifest

        result = generate_manifest(
            module_name="x_recipe",
            version="18.0.1.0.0",
            author="OdooForge",
            category="Customizations",
            description="Recipe Manager",
            depends=["base"],
            models=[SAMPLE_MODEL],
        )
        parsed = ast.literal_eval(result)
        for key in ("name", "version", "depends", "data", "installable", "license"):
            assert key in parsed, f"Missing key: {key}"

    def test_data_includes_view_and_security_paths(self):
        from odooforge.codegen.manifest_gen import generate_manifest

        result = generate_manifest(
            module_name="x_recipe",
            version="18.0.1.0.0",
            author="OdooForge",
            category="Customizations",
            description="Recipe Manager",
            depends=["base"],
            has_views=True,
            has_security=True,
            models=[SAMPLE_MODEL],
        )
        parsed = ast.literal_eval(result)
        data = parsed["data"]
        assert "security/ir.model.access.csv" in data
        assert "views/x_recipe_views.xml" in data

    def test_depends_includes_mail_for_mail_thread(self):
        from odooforge.codegen.manifest_gen import generate_manifest

        result = generate_manifest(
            module_name="x_recipe",
            version="18.0.1.0.0",
            author="OdooForge",
            category="Customizations",
            description="",
            depends=["base", "mail"],
            models=[SAMPLE_MODEL],
        )
        parsed = ast.literal_eval(result)
        assert "mail" in parsed["depends"]

    def test_security_groups_adds_security_xml_to_data(self):
        from odooforge.codegen.manifest_gen import generate_manifest

        result = generate_manifest(
            module_name="x_recipe",
            version="18.0.1.0.0",
            author="OdooForge",
            category="Customizations",
            description="",
            depends=["base"],
            models=[SAMPLE_MODEL],
            security_groups=SAMPLE_SECURITY_GROUPS,
        )
        parsed = ast.literal_eval(result)
        assert "security/x_recipe_security.xml" in parsed["data"]

    def test_no_security_groups_omits_security_xml(self):
        from odooforge.codegen.manifest_gen import generate_manifest

        result = generate_manifest(
            module_name="x_recipe",
            version="18.0.1.0.0",
            author="OdooForge",
            category="Customizations",
            description="",
            depends=["base"],
            models=[SAMPLE_MODEL],
        )
        parsed = ast.literal_eval(result)
        assert "security/x_recipe_security.xml" not in parsed["data"]


# ── TestModelGen ─────────────────────────────────────────────────


class TestModelGen:
    def test_generates_valid_python(self):
        from odooforge.codegen.model_gen import generate_models

        result = generate_models(SAMPLE_MODEL)
        # Should compile without syntax errors
        compile(result, "<test>", "exec")

    def test_class_name_is_camel_case(self):
        from odooforge.codegen.model_gen import generate_models

        result = generate_models(SAMPLE_MODEL)
        assert "class XRecipe(models.Model):" in result

    def test_includes_name_and_description(self):
        from odooforge.codegen.model_gen import generate_models

        result = generate_models(SAMPLE_MODEL)
        assert '_name = "x_recipe"' in result
        assert '_description = "Recipe"' in result

    def test_includes_inherit(self):
        from odooforge.codegen.model_gen import generate_models

        result = generate_models(SAMPLE_MODEL)
        assert "_inherit = ['mail.thread']" in result

    def test_no_inherit_when_not_specified(self):
        from odooforge.codegen.model_gen import generate_models

        result = generate_models(SAMPLE_MODEL_SIMPLE)
        assert "_inherit" not in result

    def test_field_definitions(self):
        from odooforge.codegen.model_gen import generate_models

        result = generate_models(SAMPLE_MODEL)
        assert "name = fields.Char(" in result
        assert "description = fields.Text(" in result
        assert "prep_time = fields.Integer(" in result

    def test_many2one_includes_relation(self):
        from odooforge.codegen.model_gen import generate_models

        result = generate_models(SAMPLE_MODEL)
        assert "category_id = fields.Many2one(" in result
        assert "'x_recipe.category'" in result

    def test_selection_includes_options(self):
        from odooforge.codegen.model_gen import generate_models

        result = generate_models(SAMPLE_MODEL)
        assert "stage = fields.Selection(" in result
        assert "draft" in result
        assert "active" in result

    def test_models_init_imports_all(self):
        from odooforge.codegen.model_gen import generate_models_init

        result = generate_models_init([SAMPLE_MODEL, SAMPLE_MODEL_SIMPLE])
        assert "from . import x_recipe" in result
        assert "from . import x_tag" in result

    def test_top_init_imports_models(self):
        from odooforge.codegen.model_gen import generate_top_init

        result = generate_top_init()
        assert "from . import models" in result

    def test_dotted_model_name_class(self):
        from odooforge.codegen.model_gen import _to_class_name

        assert _to_class_name("x_recipe.category") == "XRecipeCategory"

    def test_required_field_attribute(self):
        from odooforge.codegen.model_gen import generate_models

        result = generate_models(SAMPLE_MODEL)
        # The name field is required
        assert "required=True" in result


# ── TestViewGen ──────────────────────────────────────────────────


class TestViewGen:
    def test_generates_valid_xml(self):
        from odooforge.codegen.view_gen import generate_views

        result = generate_views(SAMPLE_MODEL)
        ET.fromstring(result)

    def test_includes_tree_view(self):
        from odooforge.codegen.view_gen import generate_views

        result = generate_views(SAMPLE_MODEL)
        root = ET.fromstring(result)
        tree_views = [
            r for r in root.findall("record")
            if r.get("id") == "x_recipe_view_tree"
        ]
        assert len(tree_views) == 1

    def test_includes_form_view(self):
        from odooforge.codegen.view_gen import generate_views

        result = generate_views(SAMPLE_MODEL)
        root = ET.fromstring(result)
        form_views = [
            r for r in root.findall("record")
            if r.get("id") == "x_recipe_view_form"
        ]
        assert len(form_views) == 1

    def test_includes_search_view(self):
        from odooforge.codegen.view_gen import generate_views

        result = generate_views(SAMPLE_MODEL)
        root = ET.fromstring(result)
        search_views = [
            r for r in root.findall("record")
            if r.get("id") == "x_recipe_view_search"
        ]
        assert len(search_views) == 1

    def test_includes_action(self):
        from odooforge.codegen.view_gen import generate_views

        result = generate_views(SAMPLE_MODEL)
        root = ET.fromstring(result)
        actions = [
            r for r in root.findall("record")
            if r.get("id") == "x_recipe_action"
        ]
        assert len(actions) == 1

    def test_includes_menuitem(self):
        from odooforge.codegen.view_gen import generate_views

        result = generate_views(SAMPLE_MODEL)
        root = ET.fromstring(result)
        menus = root.findall("menuitem")
        assert len(menus) == 1
        assert menus[0].get("action") == "x_recipe_action"

    def test_form_has_chatter_for_mail_thread(self):
        from odooforge.codegen.view_gen import generate_views

        result = generate_views(SAMPLE_MODEL)
        assert "oe_chatter" in result
        assert "message_ids" in result

    def test_form_no_chatter_without_mail_thread(self):
        from odooforge.codegen.view_gen import generate_views

        result = generate_views(SAMPLE_MODEL_SIMPLE)
        assert "oe_chatter" not in result

    def test_field_names_in_views(self):
        from odooforge.codegen.view_gen import generate_views

        result = generate_views(SAMPLE_MODEL)
        assert 'name="name"' in result
        assert 'name="description"' in result
        assert 'name="prep_time"' in result


# ── TestSecurityGen ──────────────────────────────────────────────


class TestSecurityGen:
    def test_csv_has_header(self):
        from odooforge.codegen.security_gen import generate_access_csv

        result = generate_access_csv([SAMPLE_MODEL])
        lines = result.strip().split("\n")
        assert lines[0] == "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink"

    def test_csv_has_user_and_manager_lines(self):
        from odooforge.codegen.security_gen import generate_access_csv

        result = generate_access_csv([SAMPLE_MODEL])
        assert "access_x_recipe_user" in result
        assert "access_x_recipe_manager" in result

    def test_csv_user_no_unlink(self):
        from odooforge.codegen.security_gen import generate_access_csv

        result = generate_access_csv([SAMPLE_MODEL])
        lines = result.strip().split("\n")
        user_line = [l for l in lines if "user" in l and "manager" not in l][0]
        assert user_line.endswith("1,1,1,0")

    def test_csv_manager_full_access(self):
        from odooforge.codegen.security_gen import generate_access_csv

        result = generate_access_csv([SAMPLE_MODEL])
        lines = result.strip().split("\n")
        manager_line = [l for l in lines if "manager" in l][0]
        assert manager_line.endswith("1,1,1,1")

    def test_security_xml_includes_groups(self):
        from odooforge.codegen.security_gen import generate_security_xml

        result = generate_security_xml("x_recipe", SAMPLE_SECURITY_GROUPS)
        root = ET.fromstring(result)
        records = root.findall("record")
        assert len(records) == 2

    def test_security_xml_group_names(self):
        from odooforge.codegen.security_gen import generate_security_xml

        result = generate_security_xml("x_recipe", SAMPLE_SECURITY_GROUPS)
        assert "Recipe User" in result
        assert "Recipe Manager" in result

    def test_security_xml_implied_group(self):
        from odooforge.codegen.security_gen import generate_security_xml

        result = generate_security_xml("x_recipe", SAMPLE_SECURITY_GROUPS)
        assert "base.group_user" in result

    def test_security_xml_valid(self):
        from odooforge.codegen.security_gen import generate_security_xml

        result = generate_security_xml("x_recipe", SAMPLE_SECURITY_GROUPS)
        ET.fromstring(result)


# ── TestAddonBuilder ─────────────────────────────────────────────


class TestAddonBuilder:
    def test_returns_all_expected_file_keys(self):
        from odooforge.codegen.addon_builder import build_addon

        result = build_addon(
            module_name="x_recipe",
            models=[SAMPLE_MODEL],
            description="Recipe Manager",
        )
        files = result["files"]
        expected_keys = {
            "__manifest__.py",
            "__init__.py",
            "models/__init__.py",
            "models/x_recipe.py",
            "views/x_recipe_views.xml",
            "security/ir.model.access.csv",
        }
        assert expected_keys.issubset(set(files.keys())), (
            f"Missing keys: {expected_keys - set(files.keys())}"
        )

    def test_summary_counts_correct(self):
        from odooforge.codegen.addon_builder import build_addon

        result = build_addon(
            module_name="x_recipe",
            models=[SAMPLE_MODEL],
            description="Recipe Manager",
        )
        summary = result["summary"]
        assert summary["models"] == 1
        assert summary["fields"] == 5
        assert summary["views"] == 3
        assert summary["security_groups"] == 0

    def test_auto_detects_mail_dependency(self):
        from odooforge.codegen.addon_builder import build_addon

        result = build_addon(
            module_name="x_recipe",
            models=[SAMPLE_MODEL],
        )
        manifest = ast.literal_eval(result["files"]["__manifest__.py"])
        assert "mail" in manifest["depends"]

    def test_default_depends_is_base(self):
        from odooforge.codegen.addon_builder import build_addon

        result = build_addon(
            module_name="x_tag",
            models=[SAMPLE_MODEL_SIMPLE],
        )
        manifest = ast.literal_eval(result["files"]["__manifest__.py"])
        assert manifest["depends"] == ["base"]

    def test_handles_multiple_models(self):
        from odooforge.codegen.addon_builder import build_addon

        result = build_addon(
            module_name="x_recipe",
            models=[SAMPLE_MODEL, SAMPLE_MODEL_SIMPLE],
        )
        files = result["files"]
        assert "models/x_recipe.py" in files
        assert "models/x_tag.py" in files
        assert "views/x_recipe_views.xml" in files
        assert "views/x_tag_views.xml" in files
        assert result["summary"]["models"] == 2
        assert result["summary"]["views"] == 6
        assert result["summary"]["fields"] == 7

    def test_handles_security_groups(self):
        from odooforge.codegen.addon_builder import build_addon

        result = build_addon(
            module_name="x_recipe",
            models=[SAMPLE_MODEL],
            security_groups=SAMPLE_SECURITY_GROUPS,
        )
        files = result["files"]
        assert "security/x_recipe_security.xml" in files
        assert result["summary"]["security_groups"] == 2

    def test_module_name_in_result(self):
        from odooforge.codegen.addon_builder import build_addon

        result = build_addon(
            module_name="x_recipe",
            models=[SAMPLE_MODEL],
        )
        assert result["module_name"] == "x_recipe"

    def test_explicit_depends_not_overridden(self):
        from odooforge.codegen.addon_builder import build_addon

        result = build_addon(
            module_name="x_recipe",
            models=[SAMPLE_MODEL],
            depends=["base", "sale"],
        )
        manifest = ast.literal_eval(result["files"]["__manifest__.py"])
        assert manifest["depends"] == ["base", "sale"]


# ── TestCodegenToolWrapper ───────────────────────────────────────


class TestCodegenToolWrapper:
    def test_async_wrapper_returns_same_as_builder(self):
        from odooforge.codegen.addon_builder import build_addon
        from odooforge.tools.codegen import odoo_generate_addon

        expected = build_addon(
            module_name="x_recipe",
            models=[SAMPLE_MODEL],
            version="18.0.1.0.0",
            author="OdooForge",
            category="Customizations",
            description="Recipe Manager",
        )

        result = asyncio.run(
            odoo_generate_addon(
                module_name="x_recipe",
                models=[SAMPLE_MODEL],
                version="18.0.1.0.0",
                author="OdooForge",
                category="Customizations",
                description="Recipe Manager",
            )
        )

        assert result == expected
