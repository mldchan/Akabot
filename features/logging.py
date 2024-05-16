import discord
from discord.ext import commands as commands_ext

from utils.blocked import is_blocked
from utils.settings import get_setting, set_setting


async def log_into_logs(server: discord.Guild, message: discord.Embed):
    log_id = get_setting(server.id, 'logging_channel', '0')
    log_chan = server.get_channel(int(log_id))
    if log_chan is None:
        return

    if not log_chan.permissions_for(server.me).send_messages:
        return

    await log_chan.send(embed=message)


class Logging(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        super().__init__()

    @discord.Cog.listener()
    @is_blocked()
    async def on_guild_emojis_update(self, guild: discord.Guild, before: discord.Emoji | None,
                                     after: discord.Emoji | None):
        if before is None and after is not None:
            embed = discord.Embed(title=f"{after} Emoji Added", color=discord.Color.green())
            embed.description = f"An emoji named {after.name}, which is {'not' if not after.animated else ''} animated, was added"
            await log_into_logs(guild, embed)

        if before is not None and after is None:
            embed = discord.Embed(title=f"{before} Emoji Removed", color=discord.Color.red())
            embed.description = f"An emoji named {before.name}, which is {'not' if not before.animated else ''} animated, was removed"
            await log_into_logs(guild, embed)

        if before is not None and after is not None:
            embed = discord.Embed(title=f"{before} Emoji Renamed", color=discord.Color.blue())
            if before.name != after.name:
                embed.add_field(name="Name", value=f'{before.name} -> {after.name}')

            await log_into_logs(guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_guild_stickers_update(self, guild: discord.Guild, before: discord.Sticker | None,
                                       after: discord.Sticker | None):
        if before is None and after is not None:
            embed = discord.Embed(title=f"{after} Sticker Added", color=discord.Color.green())
            embed.description = f"A sticker named {after.name} was added"
            await log_into_logs(guild, embed)

        if before is not None and after is None:
            embed = discord.Embed(title=f"{before} Sticker Removed", color=discord.Color.red())
            embed.description = f"A sticker named {before.name} was removed"
            await log_into_logs(guild, embed)

        if before is not None and after is not None:
            embed = discord.Embed(title=f"{before} Sticker Edited", color=discord.Color.blue())
            if before.name != after.name:
                embed.add_field(name="Name", value=f'{before.name} -> {after.name}')

            if before.description != after.description:
                embed.add_field(name="Description", value=f'{before.description} -> {after.description}')

            await log_into_logs(guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_auto_moderation_rule_create(self, rule: discord.AutoModRule):
        embed = discord.Embed(title=f"Auto Moderation Rule Created", color=discord.Color.green())
        embed.add_field(name="Rule Name", value=rule.name)
        await log_into_logs(rule.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_auto_moderation_rule_delete(self, rule: discord.AutoModRule):
        embed = discord.Embed(title=f"Auto Moderation Rule Deleted", color=discord.Color.red())
        embed.add_field(name="Rule Name", value=rule.name)
        await log_into_logs(rule.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_auto_moderation_rule_update(self, rule: discord.AutoModRule):
        embed = discord.Embed(title=f"Auto Moderation Rule Updated", color=discord.Color.blue())
        embed.add_field(name="Rule Name", value=rule.name)
        await log_into_logs(rule.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        reason = None
        moderator = None

        if guild.me.guild_permissions.view_audit_log:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    moderator = entry.user
                    reason = entry.reason
                    break

        embed = discord.Embed(title=f"{user} Banned", color=discord.Color.red())
        embed.add_field(name="Victim", value=user.display_name)
        embed.add_field(name="Victim (username)", value=user.name)

        embed.add_field(name="Moderator", value=moderator.mention if moderator else "Unknown")
        embed.add_field(name="Reason", value=reason if reason else "No reason provided")
        await log_into_logs(guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        reason = None
        moderator = None

        if guild.me.guild_permissions.view_audit_log:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
                if entry.target.id == user.id:
                    moderator = entry.user
                    reason = entry.reason
                    break

        embed = discord.Embed(title=f"{user} Unbanned", color=discord.Color.green())
        embed.add_field(name="Victim", value=user.display_name)
        embed.add_field(name="Victim (username)", value=user.name)

        embed.add_field(name="Moderator", value=moderator.mention if moderator else "Unknown")
        embed.add_field(name="Reason", value=reason if reason else "No reason provided")
        await log_into_logs(guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        embed = discord.Embed(title=f"#{after.name} Channel Updated", color=discord.Color.blue())
        if before.name != after.name:
            embed.add_field(name="Name", value=f'{before.name} -> {after.name}')
        if hasattr(before, 'topic') or hasattr(after, 'topic'):
            if before.topic != after.topic:
                embed.add_field(name="Topic", value=f'{before.topic} -> {after.topic}')
        if before.category != after.category:
            embed.add_field(name="Category", value=f'{before.category} -> {after.category}')
        if len(embed.fields) > 0:
            await log_into_logs(after.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        embed = discord.Embed(title=f"#{channel.name} Channel Created", color=discord.Color.green())
        await log_into_logs(channel.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        embed = discord.Embed(title=f"#{channel.name} Channel Deleted", color=discord.Color.red())
        await log_into_logs(channel.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        embed = discord.Embed(title=f"{after.name} Server Updated", color=discord.Color.blue())

        if before.name != after.name:
            embed.add_field(name="Name", value=f'{before.name} -> {after.name}')
        if before.icon != after.icon:
            embed.add_field(name="Icon", value='Changed')
        if before.banner != after.banner:
            embed.add_field(name="Banner", value='Changed')
        if before.description != after.description:
            embed.add_field(name="Description", value=f'{before.description} -> {after.description}')
        if before.afk_channel != after.afk_channel:
            embed.add_field(name="AFK Channel", value=f'{before.afk_channel} -> {after.afk_channel}')
        if before.afk_timeout != after.afk_timeout:
            embed.add_field(name="AFK Timeout", value=f'{before.afk_timeout} -> {after.afk_timeout}')
        if before.system_channel != after.system_channel:
            embed.add_field(name="System Channel", value=f'{before.system_channel} -> {after.system_channel}')
        if before.rules_channel != after.rules_channel:
            embed.add_field(name="Rules Channel", value=f'{before.rules_channel} -> {after.rules_channel}')
        if before.public_updates_channel != after.public_updates_channel:
            embed.add_field(name="Public Updates Channel",
                            value=f'{before.public_updates_channel} -> {after.public_updates_channel}')
        if before.preferred_locale != after.preferred_locale:
            embed.add_field(name="Preferred Locale", value=f'{before.preferred_locale} -> {after.preferred_locale}')
        if before.owner != after.owner:
            embed.add_field(name="Owner", value=f'{before.owner} -> {after.owner}')
        if before.nsfw_level != after.nsfw_level:
            embed.add_field(name="NSFW Level", value=f'{before.nsfw_level} -> {after.nsfw_level}')
        if before.verification_level != after.verification_level:
            embed.add_field(name="Verification Level",
                            value=f'{before.verification_level} -> {after.verification_level}')
        if before.explicit_content_filter != after.explicit_content_filter:
            embed.add_field(name="Explicit Content Filter",
                            value=f'{before.explicit_content_filter} -> {after.explicit_content_filter}')
        if before.default_notifications != after.default_notifications:
            embed.add_field(name="Default Notifications",
                            value=f'{before.default_notifications} -> {after.default_notifications}')
        if before.mfa_level != after.mfa_level:
            embed.add_field(name="MFA Level", value=f'{before.mfa_level} -> {after.mfa_level}')

        if len(embed.fields) > 0:
            await log_into_logs(after, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_guild_role_create(self, role: discord.Role):
        embed = discord.Embed(title=f"{role.name} Role Created", color=discord.Color.green())
        await log_into_logs(role.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_guild_role_delete(self, role: discord.Role):
        embed = discord.Embed(title=f"{role.name} Role Deleted", color=discord.Color.red())
        await log_into_logs(role.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        embed = discord.Embed(title=f"{after.name} Role Updated", color=discord.Color.blue())
        if before.name != after.name:
            embed.add_field(name="Name", value=f'{before.name} -> {after.name}')
        if before.color != after.color:
            embed.add_field(name="Color", value=f'{before.color} -> {after.color}')
        if before.hoist != after.hoist:
            embed.add_field(name="Hoist", value=f'{before.hoist} -> {after.hoist}')
        if before.mentionable != after.mentionable:
            embed.add_field(name="Mentionable", value=f'{before.mentionable} -> {after.mentionable}')
        if before.permissions != after.permissions:
            changed_allow = []
            changed_deny = []

            for perm in discord.Permissions.VALID_FLAGS:
                if before.permissions[perm] == after.permissions[perm]:
                    continue
                if after.permissions[perm]:
                    changed_allow.append(perm)
                else:
                    changed_deny.append(perm)

            if len(changed_allow) > 0:
                embed.add_field(name="Allowed Permissions", value=', '.join(changed_allow))
            if len(changed_deny) > 0:
                embed.add_field(name="Denied Permissions", value=', '.join(changed_deny))

        if len(embed.fields) > 0:
            await log_into_logs(after.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_guild_role_create(self, role: discord.Role):
        embed = discord.Embed(title=f"{role.name} Role Created", color=discord.Color.green())
        await log_into_logs(role.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_guild_role_delete(self, role: discord.Role):
        embed = discord.Embed(title=f"{role.name} Role Deleted", color=discord.Color.red())
        await log_into_logs(role.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_invite_create(self, invite: discord.Invite):
        embed = discord.Embed(title=f"{invite.url} Invite Created", color=discord.Color.green())
        embed.add_field(name="Channel", value=invite.channel.mention)
        embed.add_field(name="Max Uses", value=str(invite.max_uses))
        embed.add_field(name="Max Age", value=str(invite.max_age))
        embed.add_field(name="Temporary", value=str(invite.temporary))
        await log_into_logs(invite.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_invite_delete(self, invite: discord.Invite):
        embed = discord.Embed(title=f"{invite.url} Invite Deleted", color=discord.Color.red())
        await log_into_logs(invite.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_member_join(self, member: discord.Member):
        embed = discord.Embed(title=f"{member} Joined", color=discord.Color.green())
        await log_into_logs(member.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_member_leave(self, member: discord.Member):
        embed = discord.Embed(title=f"{member} Left", color=discord.Color.red())
        await log_into_logs(member.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        embed = discord.Embed(title=f"{after} Member Updated", color=discord.Color.blue())

        if before.nick != after.nick:
            embed.add_field(name="Nickname", value=f'{before.nick} -> {after.nick}')
        if before.roles != after.roles:
            added_roles = [role.mention for role in after.roles if role not in before.roles]
            removed_roles = [role.mention for role in before.roles if role not in after.roles]
            if len(added_roles) > 0:
                embed.add_field(name="Added Roles", value=', '.join(added_roles))
            if len(removed_roles) > 0:
                embed.add_field(name="Removed Roles", value=', '.join(removed_roles))

        if len(embed.fields) > 0:
            await log_into_logs(after.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        if before is None and after is not None:
            # joined a channel
            embed = discord.Embed(title=f"{member} Joined {after.channel.name}", color=discord.Color.green())
            embed.description = f"{member} joined the voice channel {after.channel.name}"
            await log_into_logs(member.guild, embed)

        if before is not None and after is None:
            # left a channel
            embed = discord.Embed(title=f"{member} Left {before.channel.name}", color=discord.Color.red())
            embed.description = f"{member} left the voice channel {before.channel.name}"
            await log_into_logs(member.guild, embed)

        if before is not None and after is not None:
            # moved to a different channel or was muted/deafened by admin
            if before.channel != after.channel:
                embed = discord.Embed(title=f"{member} Moved to {after.channel.name}", color=discord.Color.blue())
                embed.description = f"{member} moved from {before.channel.name} to {after.channel.name}"
                await log_into_logs(member.guild, embed)
                return

            if before.mute != after.mute:
                mod = None
                if member.guild.me.guild_permissions.view_audit_log:
                    async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                        if entry.target.id == member.id:
                            mod = entry.user
                            break

                embed = discord.Embed(title=f"{member} Muted", color=discord.Color.blue())
                if mod:
                    embed.add_field(name="Moderator", value=mod.mention)
                await log_into_logs(member.guild, embed)

            if before.deaf != after.deaf:
                mod = None
                if member.guild.me.guild_permissions.view_audit_log:
                    async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                        if entry.target.id == member.id:
                            mod = entry.user
                            break

                embed = discord.Embed(title=f"{member} Deafened", color=discord.Color.blue())
                if mod:
                    embed.add_field(name="Moderator", value=mod.mention)
                await log_into_logs(member.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        embed = discord.Embed(title="Reaction Added", color=discord.Color.green())
        embed.add_field(name='Message', value=f"[jump](<{reaction.message.jump_url}>)")
        embed.add_field(name="Emoji", value=str(reaction.emoji))
        await log_into_logs(reaction.message.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User):
        embed = discord.Embed(title="Reaction Removed", color=discord.Color.red())
        embed.add_field(name='Message', value=f"[jump](<{reaction.message.jump_url}>)")
        embed.add_field(name="Emoji", value=str(reaction.emoji))
        await log_into_logs(reaction.message.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_reaction_clear(self, message: discord.Message, reactions: list[discord.Reaction]):
        if len(reactions) < 1:
            return
        embed = discord.Embed(title="Reactions Cleared", color=discord.Color.red())
        embed.add_field(name='Message', value=reactions[0].message.jump_url)
        embed.add_field(name="Total reactions removed", value=str(len(reactions)))
        await log_into_logs(message.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_reaction_clear_emoji(self, reaction: discord.Reaction):
        embed = discord.Embed(title="Reactions Cleared", color=discord.Color.red())
        embed.add_field(name='Message', value=reaction.message.jump_url)
        embed.add_field(name="Removed reaction", value=str(reaction.emoji))
        await log_into_logs(reaction.message.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_scheduled_event_create(self, event: discord.ScheduledEvent):
        embed = discord.Embed(title="Scheduled Event Created", color=discord.Color.green())
        embed.add_field(name='Name', value=event.name)
        embed.add_field(name='Description', value=event.description)
        embed.add_field(name='Location', value=event.location.value)
        embed.add_field(name='Start', value=event.start_time.strftime("%Y/%m/%d %H:%M:%S"))
        embed.add_field(name='End', value=event.end_time.strftime("%Y/%m/%d %H:%M:%S"))
        await log_into_logs(event.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        embed = discord.Embed(title="Scheduled Event Updated", color=discord.Color.blue())
        if before.name != after.name:
            embed.add_field(name="Name", value=f'{before.name} -> {after.name}')
        if before.description != after.description:
            embed.add_field(name="Description", value=f'{before.description} -> {after.description}')
        if before.location != after.location:
            embed.add_field(name="Location", value=f'{before.location.value} -> {after.location.value}')
        if before.start_time != after.start_time:
            embed.add_field(name="Start",
                            value=f'{before.start_time.strftime("%Y/%m/%d %H:%M:%S")} -> {after.start_time.strftime("%Y/%m/%d %H:%M:%S")}')
        if before.end_time != after.end_time:
            embed.add_field(name="End",
                            value=f'{before.end_time.strftime("%Y/%m/%d %H:%M:%S")} -> {after.end_time.strftime("%Y/%m/%d %H:%M:%S")}')
        if len(embed.fields) > 0:
            await log_into_logs(after.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
        embed = discord.Embed(title="Scheduled Event Deleted", color=discord.Color.red())
        embed.add_field(name='Name', value=event.name)
        embed.add_field(name='Description', value=event.description)
        embed.add_field(name='Location', value=event.location.value)
        embed.add_field(name='Start', value=event.start_time.strftime("%Y/%m/%d %H:%M:%S"))
        embed.add_field(name='End', value=event.end_time.strftime("%Y/%m/%d %H:%M:%S"))
        await log_into_logs(event.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_thread_create(self, thread: discord.Thread):
        embed = discord.Embed(title=f"{thread.name} Thread Created", color=discord.Color.green())
        embed.add_field(name="Jump to thread", value=f"[jump](<{thread.jump_url}>)")
        embed.add_field(name="Name", value=thread.name)
        await log_into_logs(thread.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_thread_delete(self, thread: discord.Thread):
        embed = discord.Embed(title=f"{thread.name} Thread Deleted", color=discord.Color.red())
        embed.add_field(name="Name", value=thread.name)
        await log_into_logs(thread.guild, embed)

    @discord.Cog.listener()
    @is_blocked()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        embed = discord.Embed(title=f"{after.name} Thread Updated", color=discord.Color.blue())
        if before.name != after.name:
            embed.add_field(name="Name", value=f'{before.name} -> {after.name}')
        if before.archived != after.archived:
            embed.add_field(name="Archived", value=f'{before.archived} -> {after.archived}')
        if before.locked != after.locked:
            embed.add_field(name="Locked", value=f'{before.locked} -> {after.locked}')
        if len(embed.fields) > 0:
            embed.add_field(name="Jump", value=f"[jump](<{after.jump_url}>)")
            await log_into_logs(after.guild, embed)

    logging_subcommand = discord.SlashCommandGroup(name='logging', description='Logging settings')

    @logging_subcommand.command(name="list", description="List the logging settings")
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @is_blocked()
    async def list_settings(self, ctx: discord.ApplicationContext):
        logging_channel = get_setting(ctx.guild.id, 'logging_channel', '0')
        embed = discord.Embed(title='Logging settings', color=discord.Color.blurple())
        if logging_channel == '0':
            embed.add_field(name='Logging Channel', value='No logging channel set')
        else:
            channel = ctx.guild.get_channel(int(logging_channel))
            if channel is not None:
                embed.add_field(name='Logging Channel', value=channel.mention)
            else:
                embed.add_field(name='Logging Channel', value='No logging channel set')
        await ctx.response.send_message(embed=embed, ephemeral=True)

    @logging_subcommand.command(name="set_channel", description="Set the logging channel")
    @commands_ext.guild_only()
    @commands_ext.has_guild_permissions(manage_guild=True)
    @commands_ext.bot_has_permissions(send_messages=True, view_channel=True)
    @is_blocked()
    async def set_logging_channel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        set_setting(ctx.guild.id, 'logging_channel', str(channel.id))
        await ctx.response.send_message(f"Logging channel was set to {channel.mention}", ephemeral=True)
