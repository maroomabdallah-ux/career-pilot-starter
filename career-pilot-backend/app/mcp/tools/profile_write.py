from typing import Any
from uuid import UUID

from mcp.server.fastmcp import FastMCP

from app.mcp.context import run_tool
from app.mcp.schemas import (
    EducationOutput,
    ExperienceOutput,
    ProfileOutput,
    ProjectOutput,
    SkillOutput,
    WriteResult,
    json_output,
)
from app.schemas.career_profile import CareerProfileUpdate
from app.schemas.education import EducationCreate, EducationUpdate
from app.schemas.experience import ExperienceCreate, ExperienceUpdate
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.skill import SkillCreate, SkillUpdate
from app.services.education import EducationService
from app.services.experience import ExperienceService
from app.services.me import MeService
from app.services.project import ProjectService
from app.services.skill import SkillService


def register(server: FastMCP) -> None:
    @server.tool(structured_output=True)
    async def update_my_profile(changes: CareerProfileUpdate) -> dict[str, Any]:
        """Update approved fields on the authenticated user's Career Profile."""

        async def operation(session, user):
            item = await MeService(session, user).update_profile(changes)
            return _result("update", "profile", "Career Profile", item, ProfileOutput)

        return await run_tool("update_my_profile", operation)

    @server.tool(structured_output=True)
    async def add_my_skill(data: SkillCreate) -> dict[str, Any]:
        """Add one approved skill to the authenticated user's profile."""
        return await run_tool(
            "add_my_skill",
            lambda session, user: _create_child(
                session,
                user,
                SkillService(session),
                "create_skill",
                data,
                "skill",
                "name",
                SkillOutput,
            ),
        )

    @server.tool(structured_output=True)
    async def update_my_skill(skill_id: UUID, changes: SkillUpdate) -> dict[str, Any]:
        """Update one approved, authenticated-user-owned skill."""
        return await run_tool(
            "update_my_skill",
            lambda session, user: _update_child(
                session,
                user,
                SkillService(session),
                "get_skill",
                "update_skill",
                skill_id,
                changes,
                "skill",
                "name",
                SkillOutput,
            ),
        )

    @server.tool(structured_output=True)
    async def delete_my_skill(skill_id: UUID) -> dict[str, Any]:
        """Delete one approved, authenticated-user-owned skill."""
        return await run_tool(
            "delete_my_skill",
            lambda session, user: _delete_child(
                session,
                user,
                SkillService(session),
                "get_skill",
                "delete_skill",
                skill_id,
                "skill",
                "name",
            ),
        )

    _register_child_group(
        server,
        "experience",
        ExperienceService,
        "experience",
        ExperienceCreate,
        ExperienceUpdate,
        ExperienceOutput,
        "company",
    )
    _register_child_group(
        server,
        "education",
        EducationService,
        "education",
        EducationCreate,
        EducationUpdate,
        EducationOutput,
        "institution",
    )
    _register_child_group(
        server,
        "project",
        ProjectService,
        "project",
        ProjectCreate,
        ProjectUpdate,
        ProjectOutput,
        "name",
    )


def _register_child_group(
    server, singular, service_type, method_noun, create_schema, update_schema, output_schema, label
):
    create_method = f"create_{method_noun}"
    get_method = f"get_{method_noun}"
    update_method = f"update_{method_noun}"
    delete_method = f"delete_{method_noun}"

    async def add(data):
        return await run_tool(
            f"add_my_{singular}",
            lambda session, user: _create_child(
                session,
                user,
                service_type(session),
                create_method,
                create_schema.model_validate(data),
                singular,
                label,
                output_schema,
            ),
        )

    async def update(item_id: UUID, changes):
        return await run_tool(
            f"update_my_{singular}",
            lambda session, user: _update_child(
                session,
                user,
                service_type(session),
                get_method,
                update_method,
                item_id,
                update_schema.model_validate(changes),
                singular,
                label,
                output_schema,
            ),
        )

    async def delete(item_id: UUID):
        return await run_tool(
            f"delete_my_{singular}",
            lambda session, user: _delete_child(
                session,
                user,
                service_type(session),
                get_method,
                delete_method,
                item_id,
                singular,
                label,
            ),
        )

    add.__name__ = f"add_my_{singular}"
    add.__doc__ = f"Add one approved {singular} to the authenticated user's profile."
    add.__annotations__ = {"data": create_schema, "return": dict[str, Any]}
    update.__name__ = f"update_my_{singular}"
    update.__doc__ = f"Update one approved, authenticated-user-owned {singular}."
    update.__annotations__ = {
        "item_id": UUID,
        "changes": update_schema,
        "return": dict[str, Any],
    }
    delete.__name__ = f"delete_my_{singular}"
    delete.__doc__ = f"Delete one approved, authenticated-user-owned {singular}."
    delete.__annotations__ = {"item_id": UUID, "return": dict[str, Any]}
    server.tool(name=add.__name__, structured_output=True)(add)
    server.tool(name=update.__name__, structured_output=True)(update)
    server.tool(name=delete.__name__, structured_output=True)(delete)


async def _create_child(session, user, service, method, data, resource, label, output_schema):
    item = await MeService(session, user).create_child(service, method, data)
    return _result("create", resource, getattr(item, label), item, output_schema)


async def _update_child(
    session,
    user,
    service,
    get_method,
    update_method,
    item_id,
    changes,
    resource,
    label,
    output_schema,
):
    item = await MeService(session, user).update_child(
        service, get_method, update_method, item_id, changes
    )
    return _result("update", resource, getattr(item, label), item, output_schema)


async def _delete_child(
    session, user, service, get_method, delete_method, item_id, resource, label
):
    me = MeService(session, user)
    item = await me.owned_child(service, get_method, item_id)
    item_label = getattr(item, label)
    await me.delete_child(service, get_method, delete_method, item_id)
    return json_output(WriteResult(operation="delete", resource=resource, label=str(item_label)))


def _result(operation, resource, label, item, output_schema):
    clean_item = output_schema.model_validate(item).model_dump(mode="json")
    return json_output(
        WriteResult(
            operation=operation,
            resource=resource,
            label=str(label),
            item=clean_item,
        )
    )
