import {
    ChatInputCommandInteraction,
    CacheType,
    ButtonInteraction,
    Role,
    Channel,
    Message,
    GuildMember,
    EmbedBuilder,
    AuditLogEvent,
    APIEmbedField,
    PartialMessage,
    PartialGuildMember,
    PermissionsString,
    PermissionFlagsBits,
    GuildChannel,
    ChannelType,
    Guild,
    Emoji,
    Sticker,
    GuildEmoji
} from "discord.js";
import { AllCommands, Module } from "./type";
import { getSetting } from "../data/settings";

export class Logging implements Module {
    commands: AllCommands = [];
    selfMemberId: string = "";
    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {}
    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {}
    async onRoleCreate(role: Role): Promise<void> {
        const selfMember = role.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        let creator = "No Audit Log Permission";
        await selfMember.fetch(true);
        if (selfMember.permissions.has("ViewAuditLog") || selfMember.permissions.has("Administrator")) {
            const auditLog = await role.guild.fetchAuditLogs({
                type: AuditLogEvent.RoleCreate,
                limit: 1
            });
            const entry = auditLog.entries.first();
            if (entry) {
                creator = entry.executor?.username ?? "Unknown";
            }
        }

        const logChannel = getSetting(role.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = role.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        const embed = new EmbedBuilder()
            .setTitle("Role created")
            .setDescription("A new role was created")
            .addFields(
                { name: "Role name", value: role.name },
                { name: "Role ID", value: role.id },
                { name: "Role color", value: role.hexColor },
                { name: "Creator", value: creator }
            )
            .setColor("Green");

        try {
            await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onRoleEdit(before: Role, after: Role): Promise<void> {
        const selfMember = after.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        let editor = "No Audit Log Permission";
        await selfMember.fetch(true);
        if (selfMember.permissions.has("ViewAuditLog") || selfMember.permissions.has("Administrator")) {
            const auditLog = await after.guild.fetchAuditLogs({
                type: AuditLogEvent.RoleUpdate,
                limit: 1
            });
            const entry = auditLog.entries.first();
            if (entry) {
                editor = entry.executor?.username ?? "Unknown";
            }
        }

        const logChannel = getSetting(after.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = after.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        let fields: APIEmbedField[] = [];
        fields.push({ name: "Role name", value: after.name });
        if (before.name !== after.name) {
            fields.push({
                name: "Changed: Name",
                value: `${before.name} -> ${after.name}`
            });
        }
        if (before.hexColor !== after.hexColor) {
            fields.push({
                name: "Changed: Color",
                value: `${before.hexColor} -> ${after.hexColor}`
            });
        }
        const added: PermissionsString[] = [];
        const removed: PermissionsString[] = [];
        after.permissions.toArray().forEach((permission) => {
            if (!before.permissions.has(permission)) added.push(permission);
        });
        before.permissions.toArray().forEach((perm) => {
            if (!after.permissions.has(perm)) removed.push(perm);
        });
        if (added.length > 0) {
            fields.push({
                name: "Changed: Added Permissions",
                value: added.join(", ")
            });
        }
        if (removed.length > 0) {
            fields.push({
                name: "Changed: Removed Permissions",
                value: removed.join(", ")
            });
        }

        if (before.hoist !== after.hoist) {
            fields.push({
                name: "Role hoisted",
                value: `${before.hoist ? "yes" : "no"} -> ${after.hoist ? "yes" : "no"}`
            });
        }
        if (before.mentionable !== after.mentionable) {
            fields.push({
                name: "Role mentionable",
                value: `${before.mentionable ? "yes" : "no"} -> ${after.mentionable ? "yes" : "no"}`
            });
        }

        if (fields.length <= 1) return;

        fields.push({
            name: "Editor",
            value: editor
        });

        const embed = new EmbedBuilder().setTitle("Role edited").setDescription("A role was edited").addFields(fields).setColor("Yellow");
        try {
            await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onRoleDelete(role: Role): Promise<void> {
        const selfMember = role.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        let deleter = "No Audit Log Permission";
        await selfMember.fetch(true);
        if (selfMember.permissions.has("ViewAuditLog") || selfMember.permissions.has("Administrator")) {
            const auditLog = await role.guild.fetchAuditLogs({
                type: AuditLogEvent.RoleDelete,
                limit: 1
            });
            const entry = auditLog.entries.first();
            if (entry) {
                deleter = entry.executor?.username ?? "Unknown";
            }
        }

        const logChannel = getSetting(role.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = role.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        const embed = new EmbedBuilder()
            .setTitle("Role deleted")
            .setDescription("A role was deleted")
            .addFields(
                { name: "Role name", value: role.name },
                { name: "Role ID", value: role.id },
                { name: "Role color", value: role.hexColor },
                { name: "Deleter", value: deleter }
            )
            .setColor("Red");
        try {
            await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onChannelCreate(channel1: Channel): Promise<void> {
        if (channel1.isDMBased()) return;
        const selfMember = channel1.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        let creator = "No Audit Log Permission";
        await selfMember.fetch(true);
        if (selfMember.permissions.has("ViewAuditLog") || selfMember.permissions.has("Administrator")) {
            const auditLog = await channel1.guild.fetchAuditLogs({
                type: AuditLogEvent.ChannelCreate,
                limit: 1
            });
            const entry = auditLog.entries.first();
            if (entry) {
                creator = entry.executor?.username ?? "Unknown";
            }
        }

        const logChannel = getSetting(channel1.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = channel1.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        const embed = new EmbedBuilder()
            .setTitle("Channel created")
            .setDescription("A new channel was created")
            .addFields(
                { name: "Channel name", value: channel1.name },
                { name: "Channel ID", value: channel1.id.toString() },
                { name: "Channel type", value: channel1.type.toString() },
                { name: "Creator", value: creator }
            )
            .setColor("Green");

        try {
            await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onChannelEdit(before: Channel, after: Channel): Promise<void> {
        if (before.isDMBased()) return;
        if (after.isDMBased()) return;
        if (!before.guild) return;
        if (!after.guild) return;
        const selfMember = after.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        let editor = "No Audit Log Permission";
        await selfMember.fetch(true);
        if (selfMember.permissions.has("ViewAuditLog") || selfMember.permissions.has("Administrator")) {
            const auditLog = await after.guild.fetchAuditLogs({
                type: AuditLogEvent.ChannelUpdate,
                limit: 1
            });
            const entry = auditLog.entries.first();
            if (entry) {
                editor = entry.executor?.username ?? "Unknown";
            }
        }

        const logChannel = getSetting(after.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = after.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        let fields: APIEmbedField[] = [];

        if (before.name !== after.name) {
            fields.push({
                name: "Channel name",
                value: `${before.name} -> ${after.name}`
            });
        }

        if (
            (before.type === ChannelType.GuildText && after.type === ChannelType.GuildText) ||
            (before.type === ChannelType.GuildForum && after.type === ChannelType.GuildForum)
        ) {
            if (before.topic !== after.topic) {
                fields.push({
                    name: "Channel Topic",
                    value: `${before.topic ?? "*nothing*"} -> ${after.topic ?? "*nothing*"}`
                });
            }

            if (before.rateLimitPerUser !== after.rateLimitPerUser) {
                fields.push({
                    name: "Channel Cooldown",
                    value: `${before.rateLimitPerUser} seconds -> ${after.rateLimitPerUser} seconds`
                });
            }

            if (before.nsfw !== after.nsfw) {
                fields.push({
                    name: "Channel NSFW",
                    value: `${before.nsfw ? "enabled" : "disabled"} -> ${after.nsfw ? "enabled" : "disabled"}`
                });
            }
        }

        if (before.type === ChannelType.GuildVoice && after.type === ChannelType.GuildVoice) {
            if (before.bitrate !== after.bitrate) {
                fields.push({
                    name: "Channel Bitrate",
                    value: `${before.bitrate} kbps -> ${after.bitrate} kbps`
                });
            }

            if (before.nsfw !== after.nsfw) {
                fields.push({
                    name: "Channel NSFW",
                    value: `${before.nsfw ? "enabled" : "disabled"} -> ${after.nsfw ? "enabled" : "disabled"}`
                });
            }
        }

        const beforeGuild = before as GuildChannel;
        const afterGuild = after as GuildChannel;

        const createdOverwrites: string[] = [];
        const deletedOverwrites: string[] = [];

        beforeGuild.permissionOverwrites.cache.forEach((x) => {
            if (!afterGuild.permissionOverwrites.cache.has(x.id)) {
                const role = beforeGuild.guild.roles.cache.find((y) => y.id === x.id);
                if (role) {
                    deletedOverwrites.push(role.name);
                }
            }
        });
        afterGuild.permissionOverwrites.cache.forEach((x) => {
            if (!beforeGuild.permissionOverwrites.cache.has(x.id)) {
                const role = afterGuild.guild.roles.cache.find((y) => y.id === x.id);
                if (role) {
                    createdOverwrites.push(role.name);
                }
            } else {
                const allowedPermissions: string[] = [];
                const unsetPermissions: string[] = [];
                const deniedPermissions: string[] = [];
                const y = beforeGuild.permissionOverwrites.cache.get(x.id)!;

                x.deny.toArray().forEach((z) => {
                    if (!y.deny.has(z) && y.allow.has(z)) allowedPermissions.push(z);
                    if (!y.deny.has(z)) deniedPermissions.push(z);
                });
                x.allow.toArray().forEach((z) => {
                    if (!y.allow.has(z) && y.deny.has(z)) deniedPermissions.push(z);
                    if (!y.allow.has(z)) allowedPermissions.push(z);
                });
                y.allow.toArray().forEach((z) => {
                    if (!x.allow.has(z) && !x.deny.has(z)) unsetPermissions.push(z);
                });
                y.deny.toArray().forEach((z) => {
                    if (!x.allow.has(z) && !x.deny.has(z)) unsetPermissions.push(z);
                });

                if (allowedPermissions.length > 0) {
                    const role = afterGuild.guild.roles.cache.find((y) => y.id === x.id);
                    if (role) {
                        fields.push({
                            name: `Added Overrides for ${role.name}`,
                            value: allowedPermissions.join(", ")
                        });
                    }
                }
                if (unsetPermissions.length > 0) {
                    const role = afterGuild.guild.roles.cache.find((y) => y.id === x.id);
                    if (role) {
                        fields.push({
                            name: `Unset Overrides for ${role.name}`,
                            value: unsetPermissions.join(", ")
                        });
                    }
                }
                if (deniedPermissions.length > 0) {
                    const role = afterGuild.guild.roles.cache.find((y) => y.id === x.id);
                    if (role) {
                        fields.push({
                            name: `Denied Overrides for ${role.name}`,
                            value: deniedPermissions.join(", ")
                        });
                    }
                }
            }
        });

        if (createdOverwrites.length > 0) {
            fields.push({
                name: "Created Permission Overrides: ",
                value: createdOverwrites.join(", ")
            });
        }
        if (deletedOverwrites.length > 0) {
            fields.push({
                name: "Deleted Permission Overrides: ",
                value: deletedOverwrites.join(", ")
            });
        }

        fields.push({
            name: "Editor",
            value: editor
        });

        const embed = new EmbedBuilder()
            .setTitle("Channel edited")
            .setDescription("A channel was edited")
            .addFields(fields)
            .setColor("Yellow");
        try {
            await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onChannelDelete(channel: Channel): Promise<void> {
        if (channel.isDMBased()) return;
        const selfMember = channel.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        let deleter = "No Audit Log Permission";
        await selfMember.fetch(true);
        if (selfMember.permissions.has("ViewAuditLog") || selfMember.permissions.has("Administrator")) {
            const auditLog = await channel.guild.fetchAuditLogs({
                type: AuditLogEvent.ChannelDelete,
                limit: 1
            });
            const entry = auditLog.entries.first();
            if (entry) {
                deleter = entry.executor?.username ?? "Unknown";
            }
        }

        const logChannel = getSetting(channel.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const logChannel1 = channel.guild.channels.cache.get(logChannel);
        if (!logChannel1) return;
        if (!logChannel1.isTextBased()) return;

        const embed = new EmbedBuilder()
            .setTitle("Channel deleted")
            .setDescription("A channel was deleted")
            .addFields(
                { name: "Channel name", value: channel.name },
                { name: "Channel ID", value: channel.id.toString() },
                { name: "Channel type", value: channel.type.toString() },
                { name: "Deleter", value: deleter }
            )
            .setColor("Red");

        try {
            await logChannel1.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onMessage(msg: Message<boolean>): Promise<void> {}
    async onMessageDelete(msg: Message<boolean> | PartialMessage): Promise<void> {
        if (!msg.guild) return;
        if (msg.author?.id === this.selfMemberId) return;
        const logChannel = getSetting(msg.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = msg.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        const fields: APIEmbedField[] = [];

        if (msg.author) {
            fields.push({ name: "Author", value: msg.author.username });
        }
        if (msg.content) {
            fields.push({ name: "Original message", value: msg.content });
        }

        const embed = new EmbedBuilder()
            .setTitle("Message deleted")
            .setDescription("A message was deleted")
            .addFields(fields)
            .setColor("Red");

        const selfMember = msg.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        try {
            await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onMessageEdit(before: Message<boolean> | PartialMessage, after: Message<boolean> | PartialMessage): Promise<void> {
        // detect: message content change
        if (!after.guild) return;
        if (after.author?.id === this.selfMemberId) return;
        const logChannel = getSetting(after.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = after.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        let fields: APIEmbedField[] = [];

        fields.push({ name: "Author", value: after.author?.username ?? "Unknown" });

        if (before.content !== after.content) {
            fields.push({
                name: "Message content",
                value: `${before.content} -> ${after.content}`
            });
        }
        if (fields.length === 0) return;
        const embed = new EmbedBuilder()
            .setTitle("Message edited")
            .setDescription("A message was edited")
            .addFields(fields)
            .setColor("Yellow");
        const selfMember = after.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        if (channel.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) await channel.send({ embeds: [embed] });
    }
    async onMemberJoin(member: GuildMember): Promise<void> {
        const logChannel = getSetting(member.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = member.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        const embed = new EmbedBuilder()
            .setTitle("Member joined")
            .setDescription("A member joined the server")
            .addFields({ name: "Member name", value: member.user.username }, { name: "Member ID", value: member.id })
            .setColor("Green");
        const selfMember = member.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        try {
            await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onMemberEdit(before: GuildMember | PartialGuildMember, after: GuildMember | PartialGuildMember): Promise<void> {
        // detect: nickname change and role changes
        const logChannel = getSetting(after.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = after.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        let fields: APIEmbedField[] = [];

        try {
            const update = await after.guild.fetchAuditLogs({
                type: AuditLogEvent.MemberUpdate,
                limit: 1
            });
            const entry = update.entries.first();
            if (entry) {
                fields.push({
                    name: "Moderator",
                    value: entry.executor?.username ?? "Unknown"
                });
            }
        } catch (_) {}

        fields.push({ name: "Victim", value: after.user.username });

        if (before.nickname !== after.nickname) {
            fields.push({
                name: "Nickname",
                value: `${before.nickname ?? before.user.username} -> ${after.nickname ?? after.user.username}`
            });
        }
        let added: Role[] = [],
            removed: Role[] = [];
        after.roles.cache.forEach((role) => {
            if (!before.roles.cache.has(role.id)) added.push(role);
        });
        before.roles.cache.forEach((role) => {
            if (!after.roles.cache.has(role.id)) removed.push(role);
        });
        if (added.length > 0) {
            fields.push({
                name: "Roles added",
                value: added.map((x) => x.name).join(", ")
            });
        }
        if (removed.length > 0) {
            fields.push({
                name: "Roles removed",
                value: removed.map((x) => x.name).join(", ")
            });
        }

        if (fields.length <= 2) return;
        const embed = new EmbedBuilder()
            .setTitle("Member edited")
            .setDescription("A member was edited")
            .addFields(fields)
            .setColor("Yellow");

        const selfMember = after.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        try {
            await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onMemberLeave(member: GuildMember | PartialGuildMember): Promise<void> {
        const logChannel = getSetting(member.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = member.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        const embed = new EmbedBuilder()
            .setTitle("Member left")
            .setDescription("A member left the server")
            .addFields({ name: "Member name", value: member.user.username }, { name: "Member ID", value: member.id })
            .setColor("Red");
        const selfMember = member.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        try {
            await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onGuildAdd(guild: Guild): Promise<void> {}
    async onGuildRemove(guild: Guild): Promise<void> {}
    async onGuildEdit(before: Guild, after: Guild): Promise<void> {
        // check for: name change, icon change, inactive channel and time-out change, default notification settings

        const logChannel = getSetting(after.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = after.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        const fields: APIEmbedField[] = [];
        if (before.name !== after.name) {
            fields.push({
                name: "Guild name",
                value: `${before.name} -> ${after.name}`
            });
        }
        if (before.iconURL() !== after.iconURL()) {
            fields.push({
                name: "Guild icon",
                value: `${before.iconURL() ?? "*nothing*"} -> ${after.iconURL() ?? "*nothing*"}`
            });
        }
        if (before.afkChannelId !== after.afkChannelId) {
            fields.push({
                name: "AFK channel",
                value: `${before.afkChannelId ? before.afkChannelId : "*nothing*"} -> ${
                    after.afkChannelId ? after.afkChannelId : "*nothing*"
                }`
            });
        }
        if (before.afkTimeout !== after.afkTimeout) {
            fields.push({
                name: "AFK timeout",
                value: `${before.afkTimeout} -> ${after.afkTimeout}`
            });
        }
        if (before.defaultMessageNotifications !== after.defaultMessageNotifications) {
            fields.push({
                name: "Default message notifications",
                value: `${before.defaultMessageNotifications} -> ${after.defaultMessageNotifications}`
            });
        }

        if (fields.length === 0) return;
        const embed = new EmbedBuilder()
            .setTitle("Server edited")
            .setDescription("The server was edited")
            .addFields(fields)
            .setColor("Yellow");
        const selfMember = after.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        try {
            if (channel.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onEmojiCreate(emoji: GuildEmoji): Promise<void> {
        if (!emoji.guild) return;
        const logChannel = getSetting(emoji.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = emoji.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        let moderator = "No Audit Log Permission";
        try {
            const auditLog = await emoji.guild.fetchAuditLogs({
                type: AuditLogEvent.EmojiCreate,
                limit: 1
            });
            const entry = auditLog.entries.first();
            if (entry) {
                moderator = entry.executor?.username ?? "Unknown";
            }
        } catch (_) {}

        const embed = new EmbedBuilder()
            .setTitle("Emoji created")
            .setDescription("An emoji was created")
            .addFields(
                { name: "Emoji name", value: emoji.name ?? "unknown" },
                { name: "Emoji ID", value: emoji.id },
                { name: "Creator", value: moderator }
            )
            .setColor("Green");
        const selfMember = emoji.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        try {
            await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onEmojiDelete(emoji: GuildEmoji): Promise<void> {
        if (!emoji.guild) return;
        const logChannel = getSetting(emoji.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = emoji.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        let moderator = "No Audit Log Permission";
        try {
            const auditLog = await emoji.guild.fetchAuditLogs({
                type: AuditLogEvent.EmojiDelete,
                limit: 1
            });
            const entry = auditLog.entries.first();
            if (entry) {
                moderator = entry.executor?.username ?? "Unknown";
            }
        } catch (_) {}

        const embed = new EmbedBuilder()
            .setTitle("Emoji deleted")
            .setDescription("An emoji was deleted")
            .addFields(
                { name: "Emoji name", value: emoji.name ?? "unknown" },
                { name: "Emoji ID", value: emoji.id },
                { name: "Deleter", value: moderator }
            )
            .setColor("Red");
        const selfMember = emoji.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        try {
            await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onEmojiEdit(before: GuildEmoji, after: GuildEmoji): Promise<void> {
        if (!after.guild) return;
        const logChannel = getSetting(after.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = after.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        let moderator = "No Audit Log Permission";
        try {
            const auditLog = await after.guild.fetchAuditLogs({
                type: AuditLogEvent.EmojiUpdate,
                limit: 1
            });
            const entry = auditLog.entries.first();
            if (entry) {
                moderator = entry.executor?.username ?? "Unknown";
            }
        } catch (_) {}

        const fields: APIEmbedField[] = [];

        fields.push({ name: "Emoji name", value: after.name ?? "unknown" });

        if (before.name !== after.name) {
            fields.push({
                name: "Emoji name",
                value: `${before.name ?? "unknown"} -> ${after.name ?? "unknown"}`
            });
        }

        fields.push({
            name: "Editor",
            value: moderator
        });

        const embed = new EmbedBuilder()
            .setTitle("Emoji edited")
            .setDescription("An emoji was edited")
            .addFields(fields)
            .setColor("Yellow");
        const selfMember = after.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        try {
            await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onStickerCreate(sticker: Sticker): Promise<void> {
        if (!sticker.guild) return;
        const logChannel = getSetting(sticker.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = sticker.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        let moderator = "No Audit Log Permission";
        try {
            const auditLog = await sticker.guild.fetchAuditLogs({
                type: AuditLogEvent.StickerCreate,
                limit: 1
            });
            const entry = auditLog.entries.first();
            if (entry) {
                moderator = entry.executor?.username ?? "Unknown";
            }
        } catch (_) {}

        const embed = new EmbedBuilder()
            .setTitle("Sticker created")
            .setDescription("A sticker was created")
            .addFields(
                { name: "Sticker name", value: sticker.name ?? "unknown" },
                { name: "Sticker description", value: sticker.description ?? "unknown" },
                { name: "Sticker ID", value: sticker.id },
                { name: "Creator", value: moderator }
            )
            .setColor("Green");
        const selfMember = sticker.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        try {
            await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onStickerDelete(sticker: Sticker): Promise<void> {
        if (!sticker.guild) return;
        const logChannel = getSetting(sticker.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = sticker.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        let moderator = "No Audit Log Permission";
        try {
            const auditLog = await sticker.guild.fetchAuditLogs({
                type: AuditLogEvent.StickerDelete,
                limit: 1
            });
            const entry = auditLog.entries.first();
            if (entry) {
                moderator = entry.executor?.username ?? "Unknown";
            }
        } catch (_) {}

        const embed = new EmbedBuilder()
            .setTitle("Sticker deleted")
            .setDescription("A sticker was deleted")
            .addFields(
                { name: "Sticker name", value: sticker.name ?? "unknown" },
                { name: "Sticker description", value: sticker.description ?? "unknown" },
                { name: "Sticker ID", value: sticker.id },
                { name: "Deleter", value: moderator }
            )
            .setColor("Red");
        const selfMember = sticker.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        try {
            await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {
        // detect: name change, description change
        if (!after.guild) return;
        const logChannel = getSetting(after.guild.id, "loggingChannel", "");
        if (!logChannel || logChannel === "") return;
        const channel = after.guild.channels.cache.get(logChannel);
        if (!channel) return;
        if (!channel.isTextBased()) return;

        let moderator = "No Audit Log Permission";
        try {
            const auditLog = await after.guild.fetchAuditLogs({
                type: AuditLogEvent.StickerUpdate,
                limit: 1
            });
            const entry = auditLog.entries.first();
            if (entry) {
                moderator = entry.executor?.username ?? "Unknown";
            }
        } catch (_) {}

        const fields: APIEmbedField[] = [];

        fields.push({ name: "Sticker name", value: after.name ?? "unknown" });

        if (before.name !== after.name) {
            fields.push({
                name: "Sticker name",
                value: `${before.name ?? "unknown"} -> ${after.name ?? "unknown"}`
            });
        }
        if (before.description !== after.description) {
            fields.push({
                name: "Sticker description",
                value: `${before.description ?? "unknown"} -> ${after.description ?? "unknown"}`
            });
        }

        fields.push({
            name: "Editor",
            value: moderator
        });

        const embed = new EmbedBuilder()
            .setTitle("Sticker edited")
            .setDescription("A sticker was edited")
            .addFields(fields)
            .setColor("Yellow");
        const selfMember = after.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        try {
            await channel.send({ embeds: [embed] });
        } catch (_) {}
    }
}
