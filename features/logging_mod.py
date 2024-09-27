import discord
from discord.ext import commands as commands_ext

from utils.languages import get_translation_for_key_localized as trl
from utils.logging_util import log_into_logs
from utils.settings import get_setting, set_setting


def str_channel_type(channel_type: discord.ChannelType) -> str:
    text = channel_type.name.replace('_', ' ').capitalize()
    if 'thread' not in text:
        text = text + ' Channel'
    return text


def format_perm_name(name: str) -> str:
    return name.replace('_', ' ').title()


async def format_overwrite(guild_id: int, val: bool | None) -> str:
    if val is None:
        return await trl(0, guild_id, "logging_overwrite_inherited")
    return await trl(0, guild_id, "logging_overwrite_allowed") if val else await trl(0, guild_id, "logging_overwrite_denied")


class Logging(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        super().__init__()

    @discord.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before: discord.Emoji | None, after: discord.Emoji | None):
        if before is None and after is not None:
            triggering_user = None
            if guild.me.guild_permissions.view_audit_log:
                async for action in guild.audit_logs(action=discord.AuditLogAction.emoji_create, limit=1):
                    triggering_user = action.user

            embed = discord.Embed(title=await trl(0, guild.id, "logging_emoji_added_title"), color=discord.Color.green())

            if after.animated:
                embed.description = await trl(0, guild.id, "logging_animated_emoji_added").format(name=after.name)
            else:
                embed.description = await trl(0, guild.id, "logging_emoji_added").format(name=after.name)

            embed.add_field(name=await trl(0, guild.id, 'logging_moderator'), value=triggering_user.mention if triggering_user else await trl(0, guild.id, 'logging_unknown_member'), inline=False)
            await log_into_logs(guild, embed)

        if before is not None and after is None:
            triggering_user = None
            if guild.me.guild_permissions.view_audit_log:
                async for action in guild.audit_logs(action=discord.AuditLogAction.emoji_delete, limit=1):
                    triggering_user = action.user

            embed = discord.Embed(title=await trl(0, guild.id, "logging_emoji_removed"), color=discord.Color.red())
            if before.animated:
                embed.description = await trl(0, guild.id, "logging_animated_emoji_removed").format(name=before.name)
            else:
                embed.description = await trl(0, guild.id, "logging_emoji_removed").format(name=before.name)

            embed.add_field(name=await trl(0, guild.id, 'logging_moderator'), value=triggering_user.mention if triggering_user else await trl(0, guild.id, 'logging_unknown_member'), inline=False)
            await log_into_logs(guild, embed)

        if before is not None and after is not None:
            triggering_user = None
            if guild.me.guild_permissions.view_audit_log:
                async for action in guild.audit_logs(action=discord.AuditLogAction.emoji_update, limit=1):
                    triggering_user = action.user

            embed = discord.Embed(title=await trl(0, guild.id, "logging_emoji_renamed_title"), color=discord.Color.blue())
            if before.name != after.name:
                embed.add_field(name=await trl(0, guild.id, "logging_name"), value=f'{before.name} -> {after.name}')

            if len(embed.fields) > 0:
                embed.add_field(name=await trl(0, guild.id, 'logging_moderator'), value=triggering_user.mention if triggering_user else await trl(0, guild.id, 'logging_unknown_member'), inline=False)
            await log_into_logs(guild, embed)

    @discord.Cog.listener()
    async def on_guild_stickers_update(self, guild: discord.Guild, before: discord.Sticker | None, after: discord.Sticker | None):
        if before is None and after is not None:
            triggering_user = None
            if guild.me.guild_permissions.view_audit_log:
                async for action in guild.audit_logs(action=discord.AuditLogAction.sticker_create, limit=1):
                    triggering_user = action.user

            embed = discord.Embed(title=await trl(0, guild.id, "logging_sticker_added_title"), color=discord.Color.green())
            embed.description = await trl(0, guild.id, "logging_sticker_added").format(name=after.name)

            embed.add_field(name=await trl(0, guild.id, 'logging_moderator'), value=triggering_user.mention if triggering_user else await trl(0, guild.id, 'logging_unknown_member'), inline=False)
            await log_into_logs(guild, embed)

        if before is not None and after is None:
            if guild.me.guild_permissions.view_audit_log:
                async for action in guild.audit_logs(action=discord.AuditLogAction.sticker_delete, limit=1):
                    triggering_user = action.user

            embed = discord.Embed(title=await trl(0, guild.id, "logging_sticker_removed_title"), color=discord.Color.red())
            embed.description = await trl(0, guild.id, "logging_sticker_removed").format(name=before.name)

            embed.add_field(name=await trl(0, guild.id, 'logging_moderator'), value=triggering_user.mention if triggering_user else await trl(0, guild.id, 'logging_unknown_member'), inline=False)
            await log_into_logs(guild, embed)

        if before is not None and after is not None:
            triggering_user = None
            if guild.me.guild_permissions.view_audit_log:
                async for action in guild.audit_logs(action=discord.AuditLogAction.sticker_update, limit=1):
                    triggering_user = action.user

            embed = discord.Embed(title=await trl(0, guild.id, "logging_sticker_edited"), color=discord.Color.blue())
            if before.name != after.name:
                embed.add_field(name=await trl(0, guild.id, "logging_name"), value=f'{before.name} -> {after.name}')

            if before.description != after.description:
                embed.add_field(name=await trl(0, guild.id, "description"), value=f'{before.description} -> {after.description}')

            if len(embed.fields) > 0:
                embed.add_field(name=await trl(0, guild.id, 'logging_moderator'), value=triggering_user.mention if triggering_user else await trl(0, guild.id, 'logging_unknown_member'), inline=False)
            await log_into_logs(guild, embed)

    @discord.Cog.listener()
    async def on_auto_moderation_rule_create(self, rule: discord.AutoModRule):
        moderator = None
        if rule.guild.me.guild_permissions.view_audit_log:
            async for entry in rule.guild.audit_logs(limit=1, action=discord.AuditLogAction.auto_moderation_rule_create):
                moderator = entry.user

        embed = discord.Embed(title=await trl(0, rule.guild.id, "logging_automod_rule_created"), color=discord.Color.green())
        embed.add_field(name=await trl(0, rule.guild.id, "logging_rule_name"), value=rule.name)
        embed.add_field(name=await trl(0, rule.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, rule.guild.id, "logging_unknown_member"))
        await log_into_logs(rule.guild, embed)

    @discord.Cog.listener()
    async def on_auto_moderation_rule_delete(self, rule: discord.AutoModRule):
        moderator = None
        if rule.guild.me.guild_permissions.view_audit_log:
            async for entry in rule.guild.audit_logs(limit=1, action=discord.AuditLogAction.auto_moderation_rule_delete):
                moderator = entry.user
        embed = discord.Embed(title=await trl(0, rule.guild.id, "logging_automod_rule_delete"), color=discord.Color.red())
        embed.add_field(name=await trl(0, rule.guild.id, "logging_rule_name"), value=rule.name)
        embed.add_field(name=await trl(0, rule.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, rule.guild.id, "logging_unknown_member"))
        await log_into_logs(rule.guild, embed)

    @discord.Cog.listener()
    async def on_auto_moderation_rule_update(self, rule: discord.AutoModRule):
        moderator = None
        if rule.guild.me.guild_permissions.view_audit_log:
            async for entry in rule.guild.audit_logs(limit=1, action=discord.AuditLogAction.auto_moderation_rule_update):
                moderator = entry.user
        embed = discord.Embed(title=await trl(0, rule.guild.id, "logging_automod_rule_update"), color=discord.Color.blue())
        embed.add_field(name=await trl(0, rule.guild.id, "logging_rule_name"), value=rule.name)
        embed.add_field(name=await trl(0, rule.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, rule.guild.id, "logging_unknown_member"))
        await log_into_logs(rule.guild, embed)

    @discord.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        reason = None
        moderator = None

        if guild.me.guild_permissions.view_audit_log:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    moderator = entry.user
                    reason = entry.reason
                    break

        embed = discord.Embed(title=await trl(0, guild.id, "logging_ban_add_title"), color=discord.Color.red())
        embed.add_field(name=await trl(0, guild.id, "logging_victim"), value=user.display_name)
        embed.add_field(name=await trl(0, guild.id, "logging_victim_user"), value=user.name)

        embed.add_field(name=await trl(0, guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, guild.id, "logging_unknown_member"))
        embed.add_field(name=await trl(0, guild.id, "logging_reason"), value=reason if reason else await trl(0, guild.id, "logging_no_reason"))
        await log_into_logs(guild, embed)

    @discord.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        reason = None
        moderator = None

        if guild.me.guild_permissions.view_audit_log:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
                if entry.target.id == user.id:
                    moderator = entry.user
                    reason = entry.reason
                    break

        embed = discord.Embed(title=await trl(0, guild.id, "logging_ban_remove_title"), color=discord.Color.green())
        embed.add_field(name=await trl(0, guild.id, "logging_victim"), value=user.display_name)
        embed.add_field(name=await trl(0, guild.id, "logging_victim_user"), value=user.name)

        embed.add_field(name=await trl(0, guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, guild.id, "logging_unknown_member"))
        embed.add_field(name=await trl(0, guild.id, "logging_reason"), value=reason if reason else await trl(0, guild.id, "logging_no_reason"))
        await log_into_logs(guild, embed)

    @discord.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        moderator = None
        if before.guild.me.guild_permissions.view_audit_log:
            async for entry in before.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
                if entry.target.id == after.id:
                    moderator = entry.user

        embed = discord.Embed(title=await trl(0, after.guild.id, "logging_channel_update_title"), color=discord.Color.blue())
        embed.add_field(name=await trl(0, after.guild.id, "logging_channel"), value=after.mention)

        if before.name != after.name:
            embed.add_field(name=await trl(0, after.guild.id, "logging_name"), value=f'{before.name} -> {after.name}')
        if hasattr(before, 'topic') or hasattr(after, 'topic'):
            if before.topic != after.topic:
                # Before topic
                before_topic = before.topic if hasattr(before, 'topic') else await trl(0, after.guild.id, "logging_empty_field")
                if not before_topic:
                    before_topic = await trl(0, after.guild.id, "logging_empty_field")

                # After topic
                after_topic = after.topic if hasattr(after, 'topic') else await trl(0, after.guild.id, "logging_empty_field")
                if not after_topic:
                    after_topic = await trl(0, after.guild.id, "logging_empty_field")

                # Add field
                embed.add_field(name=await trl(0, after.guild.id, "logging_topic"), value=f'{before_topic} -> {after_topic}')

        if before.category != after.category:
            embed.add_field(name=await trl(0, after.guild.id, "logging_category"), value=f'{before.category} -> {after.category}')

        if before.permissions_synced != after.permissions_synced:
            embed.add_field(name=await trl(0, after.guild.id, "logging_permissions_synced"), value=f'{before.permissions_synced} -> {after.permissions_synced}')

        if before.overwrites != after.overwrites:
            for overwrite in before.overwrites:
                if overwrite not in after.overwrites:
                    embed.add_field(name=await trl(0, after.guild.id, "logging_removed_overwrite"), value=await trl(0, after.guild.id, "logging_removed_overwrite_value").format(target=overwrite.mention))

            for overwrite in after.overwrites:
                if overwrite not in before.overwrites:
                    embed.add_field(name=await trl(0, after.guild.id, "logging_added_overwrite"), value=await trl(0, after.guild.id, "logging_added_overwrite_value").format(target=overwrite.mention))

            for i in after.overwrites.keys():
                if i not in before.overwrites.keys():
                    continue

                if before.overwrites[i] == after.overwrites[i]:
                    continue

                allow = []
                deny = []
                neutral = []

                for j in zip(before.overwrites.get(i), after.overwrites.get(i)):
                    if j[0][1] != j[1][1]:
                        if j[1][1] is None:
                            neutral.append((format_perm_name(j[0][0]), await format_overwrite(after.guild.id, j[0][1]), await format_overwrite(after.guild.id, j[1][1])))
                        elif j[1][1]:
                            allow.append((format_perm_name(j[0][0]), await format_overwrite(after.guild.id, j[0][1]), await format_overwrite(after.guild.id, j[1][1])))
                        elif not j[1][1]:
                            deny.append((format_perm_name(j[0][0]), await format_overwrite(after.guild.id, j[0][1]), await format_overwrite(after.guild.id, j[1][1])))

                changes_str = ""

                for j in allow:
                    changes_str += await trl(0, after.guild.id, "logging_overwrite_permission_changes_line").format(permission=j[0], old=str(j[1]), new=str(j[2]))

                for j in deny:
                    changes_str += await trl(0, after.guild.id, "logging_overwrite_permission_changes_line").format(permission=j[0], old=str(j[1]), new=str(j[2]))

                for j in neutral:
                    changes_str += await trl(0, after.guild.id, "logging_overwrite_permission_changes_line").format(permission=j[0], old=str(j[1]), new=str(j[2]))

                overwrite_embed = discord.Embed(title=await trl(0, after.guild.id, "logging_overwrite_update_title").format(channel=after.mention, target=i.mention), color=discord.Color.blue())

                overwrite_embed.add_field(name=await trl(0, after.guild.id, "logging_overwrite_permission_changes"), value=changes_str)

                overwrite_embed.add_field(name=await trl(0, after.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, after.guild.id, "logging_unknown_member"))

                await log_into_logs(after.guild, overwrite_embed)

        if len(embed.fields) > 1:
            embed.add_field(name=await trl(0, after.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, after.guild.id, "logging_unknown_member"))
            await log_into_logs(after.guild, embed)

    @discord.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        moderator = None
        if channel.guild.me.guild_permissions.view_audit_log:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                if entry.target.id == channel.id:
                    moderator = entry.user

        embed = discord.Embed(title=await trl(0, channel.guild.id, "logging_channel_create_title"),
                              description=await trl(0, channel.guild.id, "logging_channel_create_description").format(type=str_channel_type(channel.type), name=channel.name), color=discord.Color.green())

        embed.add_field(name=await trl(0, channel.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, channel.guild.id, "logging_unknown_member"))

        await log_into_logs(channel.guild, embed)

    @discord.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        moderator = None
        if channel.guild.me.guild_permissions.view_audit_log:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id:
                    moderator = entry.user

        embed = discord.Embed(title=await trl(0, channel.guild.id, "logging_channel_delete_title"),
                              description=await trl(0, channel.guild.id, "logging_channel_delete_description").format(type=str_channel_type(channel.type), name=channel.name), color=discord.Color.red())

        embed.add_field(name=await trl(0, channel.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, channel.guild.id, "logging_unknown_member"))

        await log_into_logs(channel.guild, embed)

    @discord.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        moderator = None
        if after.me.guild_permissions.view_audit_log:
            async for entry in after.audit_logs(limit=1, action=discord.AuditLogAction.guild_update):
                moderator = entry.user

        embed = discord.Embed(title=f"{after.name} Server Updated", color=discord.Color.blue())

        if before.name != after.name:
            embed.add_field(name=await trl(0, after.id, "logging_name"), value=f'{before.name} -> {after.name}')
        if before.icon != after.icon:
            embed.add_field(name=await trl(0, after.id, "logging_icon"), value=await trl(0, after.id, "logging_changed"))
        if before.banner != after.banner:
            embed.add_field(name=await trl(0, after.id, "logging_banner"), value=await trl(0, after.id, "logging_changed"))
        if before.description != after.description:
            embed.add_field(name=await trl(0, after.id, "description"), value=f'{before.description} -> {after.description}')
        if before.afk_channel != after.afk_channel:
            embed.add_field(name=await trl(0, after.id, "logging_afk_channel"), value=f'{before.afk_channel} -> {after.afk_channel}')
        if before.afk_timeout != after.afk_timeout:
            embed.add_field(name=await trl(0, after.id, "logging_afk_timeout"), value=f'{before.afk_timeout} -> {after.afk_timeout}')
        if before.system_channel != after.system_channel:
            embed.add_field(name=await trl(0, after.id, "logging_system_channel"), value=f'{before.system_channel} -> {after.system_channel}')
        if before.rules_channel != after.rules_channel:
            embed.add_field(name=await trl(0, after.id, "logging_rules_channel"), value=f'{before.rules_channel} -> {after.rules_channel}')
        if before.public_updates_channel != after.public_updates_channel:
            embed.add_field(name=await trl(0, after.id, "logging_public_updates_channel"), value=f'{before.public_updates_channel} -> {after.public_updates_channel}')
        if before.preferred_locale != after.preferred_locale:
            embed.add_field(name=await trl(0, after.id, "logging_preferred_locale"), value=f'{before.preferred_locale} -> {after.preferred_locale}')
        if before.owner != after.owner:
            embed.add_field(name=await trl(0, after.id, "logging_owner"), value=f'{before.owner} -> {after.owner}')
        if before.nsfw_level != after.nsfw_level:
            embed.add_field(name=await trl(0, after.id, "logging_nsfw_level"), value=f'{before.nsfw_level} -> {after.nsfw_level}')
        if before.verification_level != after.verification_level:
            embed.add_field(name=await trl(0, after.id, "logging_verification_level"), value=f'{before.verification_level} -> {after.verification_level}')
        if before.explicit_content_filter != after.explicit_content_filter:
            embed.add_field(name=await trl(0, after.id, "logging_explicit_content_filter"), value=f'{before.explicit_content_filter} -> {after.explicit_content_filter}')
        if before.default_notifications != after.default_notifications:
            embed.add_field(name=await trl(0, after.id, "logging_default_notifications"), value=f'{before.default_notifications} -> {after.default_notifications}')
        if before.mfa_level != after.mfa_level:
            embed.add_field(name=await trl(0, after.id, "logging_mfa_level"), value=f'{before.mfa_level} -> {after.mfa_level}')

        if len(embed.fields) > 0:
            embed.add_field(name=await trl(0, after.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, after.id, "logging_unknown_member"))

            await log_into_logs(after, embed)

    @discord.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        moderator = None
        if role.guild.me.guild_permissions.view_audit_log:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
                if entry.target.id == role.id:
                    moderator = entry.user

        embed = discord.Embed(title=await trl(0, role.guild.id, "logging_role_created_title"), description=await trl(0, role.guild.id, "logging_role_created_description").format(name=role.name),
                              color=discord.Color.green())

        embed.add_field(name=await trl(0, role.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, role.guild.id, "logging_unknown_member"))

        await log_into_logs(role.guild, embed)

    @discord.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        moderator = None
        if role.guild.me.guild_permissions.view_audit_log:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                if entry.target.id == role.id:
                    moderator = entry.user

        embed = discord.Embed(title=await trl(0, role.guild.id, "logging_role_deleted_title"), description=await trl(0, role.guild.id, "logging_role_deleted_description").format(name=role.name),
                              color=discord.Color.red())

        embed.add_field(name=await trl(0, role.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, role.guild.id, "logging_unknown_member"))

        await log_into_logs(role.guild, embed)

    @discord.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        moderator = None
        if after.guild.me.guild_permissions.view_audit_log:
            async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                if entry.target.id == after.id:
                    moderator = entry.user

        embed = discord.Embed(title=await trl(0, after.guild.id, "logging_role_updated_title"), color=discord.Color.blue())
        if before.name != after.name:
            embed.add_field(name=await trl(0, after.guild.id, "logging_name"), value=f'{before.name} -> {after.name}')
        if before.color != after.color:
            embed.add_field(name=await trl(0, after.guild.id, "logging_color"), value=f'{before.color} -> {after.color}')
        if before.hoist != after.hoist:
            embed.add_field(name=await trl(0, after.guild.id, "logging_hoisted"), value=f'{before.hoist} -> {after.hoist}')
        if before.mentionable != after.mentionable:
            embed.add_field(name=await trl(0, after.guild.id, "logging_mentionable"), value=f'{before.mentionable} -> {after.mentionable}')
        if before.permissions != after.permissions:
            changed_deny = []
            changed_allow = []

            for (perm, value) in iter(after.permissions):
                if value == dict(before.permissions)[perm]:
                    continue
                if dict(before.permissions)[perm]:
                    changed_deny.append(perm)
                else:
                    changed_allow.append(perm)

            changed_deny = [format_perm_name(perm) for perm in changed_deny]
            changed_allow = [format_perm_name(perm) for perm in changed_allow]

            if len(changed_deny) > 0:
                embed.add_field(name=await trl(0, after.guild.id, "logging_allowed_perms"), value=', '.join(changed_deny))
            if len(changed_allow) > 0:
                embed.add_field(name=await trl(0, after.guild.id, "logging_denied_perms"), value=', '.join(changed_allow))

        if len(embed.fields) > 0:
            embed.add_field(name=await trl(0, after.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, after.guild.id, "logging_unknown_member"))

            await log_into_logs(after.guild, embed)

    @discord.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        moderator = None
        if invite.guild.me.guild_permissions.view_audit_log:
            async for entry in invite.guild.audit_logs(limit=1, action=discord.AuditLogAction.invite_create):
                if entry.target.id == invite.id:
                    moderator = entry.user

        embed = discord.Embed(title=await trl(0, invite.guild.id, "logging_invite_created"), color=discord.Color.green())
        embed.add_field(name=await trl(0, invite.guild.id, "logging_code"), value=invite.code)
        embed.add_field(name=await trl(0, invite.guild.id, "logging_channel"), value=invite.channel.mention)
        embed.add_field(name=await trl(0, invite.guild.id, "logging_max_uses"), value=str(invite.max_uses))
        embed.add_field(name=await trl(0, invite.guild.id, "logging_max_age"), value=str(invite.max_age))
        embed.add_field(name=await trl(0, invite.guild.id, "logging_temporary"), value=str(invite.temporary))
        embed.add_field(name=await trl(0, invite.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, invite.guild.id, "logging_unknown_member"))
        await log_into_logs(invite.guild, embed)

    @discord.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        moderator = None
        if invite.guild.me.guild_permissions.view_audit_log:
            async for entry in invite.guild.audit_logs(limit=1, action=discord.AuditLogAction.invite_delete):
                if entry.target.id == invite.id:
                    moderator = entry.user

        embed = discord.Embed(title=await trl(0, invite.guild.id, "logging_invite_deleted"), color=discord.Color.red())

        embed.add_field(name=await trl(0, invite.guild.id, "logging_code"), value=invite.code)
        embed.add_field(name=await trl(0, invite.guild.id, "logging_channel"), value=invite.channel.mention)
        embed.add_field(name=await trl(0, invite.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, invite.guild.id, "logging_unknown_member"))
        await log_into_logs(invite.guild, embed)

    @discord.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        embed = discord.Embed(title=await trl(0, member.guild.id, "logging_member_join_title"), description=await trl(0, member.guild.id, "logging_member_join_description").format(mention=member.mention),
                              color=discord.Color.green())
        embed.add_field(name=await trl(0, member.guild.id, "logging_user"), value=member.mention)
        await log_into_logs(member.guild, embed)

    @discord.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        embed = discord.Embed(title=await trl(0, member.guild.id, "logging_member_leave_title"), description=await trl(0, member.guild.id, "logging_member_leave_description").format(mention=member.mention),
                              color=discord.Color.red())
        embed.add_field(name=await trl(0, member.guild.id, "logging_user"), value=member.mention)
        await log_into_logs(member.guild, embed)

    @discord.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        moderator = None
        if after.guild.me.guild_permissions.view_audit_log:
            async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                if entry.target.id == after.id:
                    moderator = entry.user

        embed = discord.Embed(title=await trl(0, after.guild.id, "logging_member_update_title"), color=discord.Color.blue())
        embed.add_field(name=await trl(0, after.guild.id, "logging_user"), value=after.mention)

        if before.nick != after.nick:
            embed.add_field(name=await trl(0, after.guild.id, "logging_nickname"), value=f'{before.nick} -> {after.nick}')
        if before.roles != after.roles:
            added_roles = [role.mention for role in after.roles if role not in before.roles]
            removed_roles = [role.mention for role in before.roles if role not in after.roles]
            if len(added_roles) > 0:
                embed.add_field(name=await trl(0, after.guild.id, "logging_added_roles"), value=', '.join(added_roles))
            if len(removed_roles) > 0:
                embed.add_field(name=await trl(0, after.guild.id, "logging_removed_roles"), value=', '.join(removed_roles))

        if len(embed.fields) > 1:
            embed.add_field(name=await trl(0, after.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, after.guild.id, "logging_unknown_member"))
            await log_into_logs(after.guild, embed)

    @discord.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel is None and after.channel is not None:
            # joined a channel
            embed = discord.Embed(title=await trl(0, member.guild.id, "logging_vc_join"),
                                  description=await trl(0, member.guild.id, "logging_vc_join_description").format(mention=member.mention, channel_mention=after.channel.mention), color=discord.Color.green())
            await log_into_logs(member.guild, embed)

        if before.channel is not None and after.channel is None:
            # left a channel
            embed = discord.Embed(title=await trl(0, member.guild.id, "logging_vc_leave"),
                                  description=await trl(0, member.guild.id, "logging_vc_leave_description").format(mention=member.mention, channel_mention=before.channel.mention), color=discord.Color.red())
            await log_into_logs(member.guild, embed)

        if before.channel is not None and after.channel is not None:
            # moved to a different channel or was muted/deafened by admin
            if before.channel != after.channel:
                embed = discord.Embed(title=await trl(0, member.guild.id, "logging_vc_move"),
                                      description=await trl(0, member.guild.id, "logging_vc_move_description").format(mention=member.mention, previous=before.channel.mention, current=after.channel.mention),
                                      color=discord.Color.blue())
                await log_into_logs(member.guild, embed)
                return

            if before.mute != after.mute:
                mod = None
                if member.guild.me.guild_permissions.view_audit_log:
                    async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                        if entry.target.id == member.id:
                            mod = entry.user
                            break

                embed = discord.Embed(title=await trl(0, member.guild.id, "logging_vc_server_mute"), color=discord.Color.blue())

                if after.mute:
                    embed.description = await trl(0, member.guild.id, "logging_vc_server_mute_description_enabled").format(mention=member.mention)
                else:
                    embed.description = await trl(0, member.guild.id, "logging_vc_server_mute_description_disabled").format(mention=member.mention)

                if mod:
                    embed.add_field(name=await trl(0, member.guild.id, "logging_moderator"), value=mod.mention)
                await log_into_logs(member.guild, embed)

            if before.deaf != after.deaf:
                mod = None
                if member.guild.me.guild_permissions.view_audit_log:
                    async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                        if entry.target.id == member.id:
                            mod = entry.user
                            break

                embed = discord.Embed(title=await trl(0, member.guild.id, "logging_vc_server_deafen"), color=discord.Color.blue())

                if after.deaf:
                    embed.description = await trl(0, member.guild.id, "logging_vc_server_deafen_description_enabled").format(mention=member.mention)
                else:
                    embed.description = await trl(0, member.guild.id, "logging_vc_server_deafen_description_disabled").format(mention=member.mention)

                if mod:
                    embed.add_field(name=await trl(0, member.guild.id, "logging_moderator"), value=mod.mention)
                await log_into_logs(member.guild, embed)

    @discord.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        embed = discord.Embed(title=await trl(0, reaction.message.guild.id, "logging_reaction_added_title"), color=discord.Color.green())
        embed.add_field(name=await trl(0, reaction.message.guild.id, "logging_message"), value=f"[jump](<{reaction.message.jump_url}>)")
        embed.add_field(name=await trl(0, reaction.message.guild.id, "logging_emoji"), value=str(reaction.emoji))
        embed.add_field(name=await trl(0, reaction.message.guild.id, "logging_user"), value=user.mention)
        await log_into_logs(reaction.message.guild, embed)

    @discord.Cog.listener()
    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User):
        embed = discord.Embed(title=await trl(0, reaction.message.guild.id, "logging_reaction_removed_title"), color=discord.Color.red())
        embed.add_field(name=await trl(0, reaction.message.guild.id, "logging_message"), value=f"[jump](<{reaction.message.jump_url}>)")
        embed.add_field(name=await trl(0, reaction.message.guild.id, "logging_emoji"), value=str(reaction.emoji))
        embed.add_field(name=await trl(0, reaction.message.guild.id, "logging_user"), value=user.mention)
        await log_into_logs(reaction.message.guild, embed)

    @discord.Cog.listener()
    async def on_reaction_clear(self, message: discord.Message, reactions: list[discord.Reaction]):
        if len(reactions) < 1:
            return
        embed = discord.Embed(title=await trl(0, message.guild.id, "logging_reactions_clear_all"), color=discord.Color.red())
        embed.add_field(name=await trl(0, message.guild.id, "logging_message"), value=reactions[0].message.jump_url)
        await log_into_logs(message.guild, embed)

    @discord.Cog.listener()
    async def on_reaction_clear_emoji(self, reaction: discord.Reaction):
        embed = discord.Embed(title=await trl(0, reaction.message.guild.id, "logging_reactions_clear"), color=discord.Color.red())
        embed.add_field(name=await trl(0, reaction.message.guild.id, "logging_message"), value=reaction.message.jump_url)
        embed.add_field(name=await trl(0, reaction.message.guild.id, "logging_emoji"), value=str(reaction.emoji))
        await log_into_logs(reaction.message.guild, embed)

    @discord.Cog.listener()
    async def on_scheduled_event_create(self, event: discord.ScheduledEvent):
        moderator = None
        if event.guild.me.guild_permissions.view_audit_log:
            async for entry in event.guild.audit_logs(limit=1, action=discord.AuditLogAction.scheduled_event_create):
                moderator = entry.user

        embed = discord.Embed(title=await trl(0, event.guild.id, "logging_scheduled_event_create"), color=discord.Color.green())
        embed.add_field(name=await trl(0, event.guild.id, "logging_name"), value=event.name)
        embed.add_field(name=await trl(0, event.guild.id, "description"), value=event.description)
        embed.add_field(name=await trl(0, event.guild.id, "logging_location"), value=event.location.value)
        embed.add_field(name=await trl(0, event.guild.id, "logging_start"), value=event.start_time.strftime("%Y/%m/%d %H:%M:%S"))
        embed.add_field(name=await trl(0, event.guild.id, "logging_end"), value=event.end_time.strftime("%Y/%m/%d %H:%M:%S"))
        embed.add_field(name=await trl(0, event.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, event.guild.id, "logging_unknown_member"))
        await log_into_logs(event.guild, embed)

    @discord.Cog.listener()
    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        moderator = None
        if after.guild.me.guild_permissions.view_audit_log:
            async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.scheduled_event_update):
                moderator = entry.user

        embed = discord.Embed(title=await trl(0, after.guild.id, "logging_scheduled_event_update"), color=discord.Color.blue())
        if before.name != after.name:
            embed.add_field(name=await trl(0, after.guild.id, "logging_name"), value=f'{before.name} -> {after.name}')
        if before.description != after.description:
            embed.add_field(name=await trl(0, after.guild.id, "description"), value=f'{before.description} -> {after.description}')
        if before.location != after.location:
            embed.add_field(name=await trl(0, after.guild.id, "logging_location"), value=f'{before.location.value} -> {after.location.value}')
        if before.start_time != after.start_time:
            embed.add_field(name=await trl(0, after.guild.id, "logging_start"), value=f'{before.start_time.strftime("%Y/%m/%d %H:%M:%S")} -> {after.start_time.strftime("%Y/%m/%d %H:%M:%S")}')
        if before.end_time != after.end_time:
            embed.add_field(name=await trl(0, after.guild.id, "logging_end"), value=f'{before.end_time.strftime("%Y/%m/%d %H:%M:%S")} -> {after.end_time.strftime("%Y/%m/%d %H:%M:%S")}')
        if len(embed.fields) > 0:
            embed.add_field(name=await trl(0, after.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, after.guild.id, "logging_unknown_member"))
            await log_into_logs(after.guild, embed)

    @discord.Cog.listener()
    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
        moderator = None
        if event.guild.me.guild_permissions.view_audit_log:
            async for entry in event.guild.audit_logs(limit=1, action=discord.AuditLogAction.scheduled_event_delete):
                moderator = entry.user

        embed = discord.Embed(title=await trl(0, event.guild.id, "logging_scheduled_event_delete"), color=discord.Color.red())
        embed.add_field(name=await trl(0, event.guild.id, "logging_name"), value=event.name)
        embed.add_field(name=await trl(0, event.guild.id, "description"), value=event.description)
        embed.add_field(name=await trl(0, event.guild.id, "logging_location"), value=event.location.value)
        embed.add_field(name=await trl(0, event.guild.id, "logging_start"), value=event.start_time.strftime("%Y/%m/%d %H:%M:%S"))
        embed.add_field(name=await trl(0, event.guild.id, "logging_end"), value=event.end_time.strftime("%Y/%m/%d %H:%M:%S"))
        embed.add_field(name=await trl(0, event.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, event.guild.id, "logging_unknown_member"))
        await log_into_logs(event.guild, embed)

    @discord.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        moderator = None
        if thread.guild.me.guild_permissions.view_audit_log:
            async for entry in thread.guild.audit_logs(limit=1, action=discord.AuditLogAction.thread_create):
                if entry.target.id == thread.id:
                    moderator = entry.user

        embed = discord.Embed(title=await trl(0, thread.guild.id, "logging_thread_create"), description=await trl(0, thread.guild.id, "logging_thread_create_description").format(name=thread.name),
                              color=discord.Color.green())
        embed.add_field(name=await trl(0, thread.guild.id, "logging_jump_to_thread"), value=f"[jump](<{thread.jump_url}>)")
        embed.add_field(name=await trl(0, thread.guild.id, "logging_name"), value=thread.name)
        embed.add_field(name=await trl(0, thread.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, thread.guild.id, "logging_unknown_member"))
        await log_into_logs(thread.guild, embed)

    @discord.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread):
        moderator = None
        if thread.guild.me.guild_permissions.view_audit_log:
            async for entry in thread.guild.audit_logs(limit=1, action=discord.AuditLogAction.thread_delete):
                if entry.target.id == thread.id:
                    moderator = entry.user

        embed = discord.Embed(title=await trl(0, thread.guild.id, "logging_thread_delete"), description=await trl(0, thread.guild.id, "logging_thread_delete_description").format(name=thread.name),
                              color=discord.Color.red())
        embed.add_field(name=await trl(0, thread.guild.id, "logging_name"), value=thread.name)
        embed.add_field(name=await trl(0, thread.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, thread.guild.id, "logging_unknown_member"))
        await log_into_logs(thread.guild, embed)

    @discord.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        if before.guild.me.guild_permissions.view_audit_log:
            async for entry in before.guild.audit_logs(limit=1, action=discord.AuditLogAction.thread_update):
                if entry.target.id == after.id:
                    moderator = entry.user

        embed = discord.Embed(title=await trl(0, after.guild.id, "logging_thread_update"), color=discord.Color.blue())

        if before.name != after.name:
            embed.add_field(name=await trl(0, after.guild.id, "logging_name"), value=f'{before.name} -> {after.name}')
        if before.archived != after.archived:
            embed.add_field(name=await trl(0, after.guild.id, "logging_archived"), value=f'{before.archived} -> {after.archived}')
        if before.locked != after.locked:
            embed.add_field(name=await trl(0, after.guild.id, "logging_locked"), value=f'{before.locked} -> {after.locked}')
        if len(embed.fields) > 0:
            embed.add_field(name=await trl(0, after.guild.id, "logging_jump_to_thread"), value=f"[jump](<{after.jump_url}>)")
            embed.add_field(name=await trl(0, after.guild.id, "logging_moderator"), value=moderator.mention if moderator else await trl(0, after.guild.id, "logging_unknown_member"))
            await log_into_logs(after.guild, embed)

    logging_subcommand = discord.SlashCommandGroup(name='logging', description='Logging settings')

    @logging_subcommand.command(name="list", description="List the logging settings")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    async def list_settings(self, ctx: discord.ApplicationContext):
        logging_channel = await get_setting(ctx.guild.id, 'logging_channel', '0')
        embed = discord.Embed(title=await trl(ctx.user.id, ctx.guild.id, "logging_list_title"), color=discord.Color.blurple())
        if logging_channel == '0':
            embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "logging_list_channel"), value=await trl(ctx.user.id, ctx.guild.id, "logging_list_none"))
        else:
            channel = ctx.guild.get_channel(int(logging_channel))
            if channel is not None:
                embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "logging_list_channel"), value=channel.mention)
            else:
                embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "logging_list_channel"), value=await trl(ctx.user.id, ctx.guild.id, "logging_list_none"))
        await ctx.respond(embed=embed, ephemeral=True)

    @logging_subcommand.command(name="set_channel", description="Set the logging channel")
    @commands_ext.guild_only()
    @commands_ext.has_guild_permissions(manage_guild=True)
    @commands_ext.bot_has_permissions(send_messages=True, view_channel=True)
    async def set_logging_channel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        # Get old channel
        old_channel_id = await get_setting(ctx.guild.id, "logging_channel", str(channel.id))
        old_channel = ctx.guild.get_channel(int(old_channel_id))

        # New channel
        await set_setting(ctx.guild.id, 'logging_channel', str(channel.id))

        logging_embed = discord.Embed(title=await trl(ctx.user.id, ctx.guild.id, "logging_set_channel_log_title"))
        logging_embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        if old_channel is not None:
            logging_embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "logging_set_channel_previous"), value=f"{old_channel.mention}")

        # Send into logs
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "logging_set_channel_success").format(channel=channel.mention), ephemeral=True)
