import {
    APIEmbedField,
    AttachmentBuilder,
    AuditLogEvent,
    ButtonInteraction,
    Channel,
    ChannelType,
    ChatInputCommandInteraction, Client,
    EmbedBuilder,
    Guild,
    GuildChannel,
    GuildEmoji,
    GuildMember,
    Message,
    PartialGuildMember,
    PartialMessage,
    PermissionFlagsBits,
    PermissionsString,
    Role,
    Sticker
} from "discord.js";
import { AllCommands, Module } from "./type";
import { fetchAuditLog, getLogChannel, getSelfMember } from "../utilities/useful";

export class Logging implements Module {
    commands: AllCommands = [];
    selfMemberId: string = "";

    async onSlashCommand(interaction: ChatInputCommandInteraction): Promise<void> {
    }

    async onButtonClick(interaction: ButtonInteraction): Promise<void> {
    }

    async onRoleCreate(role: Role): Promise<void> {
        const selfMember = getSelfMember(role.guild);
        if (!selfMember) return;
        let creator = await fetchAuditLog(role.guild, AuditLogEvent.RoleCreate);

        const channel = getLogChannel(role.guild);
        if (!channel) return;
        if (!channel.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

        const embed = new EmbedBuilder().setTitle("Role created").setDescription("A new role was created").addFields({
            name: "Role name",
            value: role.name
        }, { name: "Role ID", value: role.id }, { name: "Role color", value: role.hexColor }, {
            name: "Creator",
            value: creator
        }).setColor("Green");

        await channel.send({ embeds: [embed] });
    }

    async onRoleEdit(before: Role, after: Role): Promise<void> {
        const selfMember = getSelfMember(after.guild);
        if (!selfMember) return;
        let editor = await fetchAuditLog(after.guild, AuditLogEvent.RoleUpdate);

        const logs = getLogChannel(after.guild);
        if (!logs) return;
        if (!logs.isTextBased()) return;
        if (!logs.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

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
        await logs.send({ embeds: [embed] });
    }

    async onRoleDelete(role: Role): Promise<void> {
        const selfMember = role.guild.members.cache.get(this.selfMemberId);
        if (!selfMember) return;
        let deleter = await fetchAuditLog(role.guild, AuditLogEvent.RoleDelete);

        const logs = getLogChannel(role.guild);
        if (!logs) return;
        if (!logs.isTextBased()) return;
        if (!logs.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

        const embed = new EmbedBuilder().setTitle("Role deleted").setDescription("A role was deleted").addFields({
            name: "Role name",
            value: role.name
        }, { name: "Role ID", value: role.id }, { name: "Role color", value: role.hexColor }, {
            name: "Deleter",
            value: deleter
        }).setColor("Red");
        await logs.send({ embeds: [embed] });
    }

    async onChannelCreate(channel: Channel): Promise<void> {
        if (channel.isDMBased()) return;
        const selfMember = getSelfMember(channel.guild);
        if (!selfMember) return;
        let creator = await fetchAuditLog(channel.guild, AuditLogEvent.ChannelCreate);

        const logs = getLogChannel(channel.guild);
        if (!logs) return;
        if (!logs.isTextBased()) return;
        if (!logs.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

        const embed = new EmbedBuilder().setTitle("Channel created").setDescription("A new channel was created").addFields({
            name: "Channel name",
            value: channel.name
        }, { name: "Channel ID", value: channel.id.toString() }, {
            name: "Channel type",
            value: channel.type.toString()
        }, { name: "Creator", value: creator }).setColor("Green");

        await logs.send({ embeds: [embed] });
    }

    async onChannelEdit(before: Channel, after: Channel): Promise<void> {
        if (before.isDMBased()) return;
        if (after.isDMBased()) return;
        if (!before.guild) return;
        if (!after.guild) return;
        const selfMember = getSelfMember(after.guild);
        if (!selfMember) return;
        let editor = await fetchAuditLog(after.guild, AuditLogEvent.ChannelUpdate);

        const channel = getLogChannel(after.guild);
        if (!channel) return;
        if (!channel.isTextBased()) return;
        if (!channel.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

        let fields: APIEmbedField[] = [];

        if (before.name !== after.name) {
            fields.push({
                name: "Channel name",
                value: `${before.name} -> ${after.name}`
            });
        }

        if ((before.type === ChannelType.GuildText && after.type === ChannelType.GuildText) || (before.type === ChannelType.GuildForum && after.type === ChannelType.GuildForum)) {
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

        const embed = new EmbedBuilder().setTitle("Channel edited").setDescription("A channel was edited").addFields(fields).setColor("Yellow");
        await channel.send({ embeds: [embed] });
    }

    async onChannelDelete(channel: Channel): Promise<void> {
        if (channel.isDMBased()) return;
        const selfMember = getSelfMember(channel.guild);
        if (!selfMember) return;
        let deleter = await fetchAuditLog(channel.guild, AuditLogEvent.ChannelDelete);

        const logs = getLogChannel(channel.guild);
        if (!logs) return;
        if (!logs.isTextBased()) return;

        const embed = new EmbedBuilder().setTitle("Channel deleted").setDescription("A channel was deleted").addFields({
            name: "Channel name",
            value: channel.name
        }, { name: "Channel ID", value: channel.id.toString() }, {
            name: "Channel type",
            value: channel.type.toString()
        }, { name: "Deleter", value: deleter }).setColor("Red");

        await logs.send({ embeds: [embed] });
    }

    async onMessage(msg: Message): Promise<void> {
    }

    async onMessageDelete(msg: Message | PartialMessage): Promise<void> {
        if (!msg.guild) return;
        const selfMember = getSelfMember(msg.guild);
        if (!selfMember) return;
        if (msg.author?.id === selfMember.id) return;
        const channel = getLogChannel(msg.guild);
        if (!channel) return;
        if (!channel.isTextBased()) return;
        if (!channel.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

        const fields: APIEmbedField[] = [];

        if (msg.author) {
            fields.push({ name: "Message Author", value: msg.author.username });
        }
        if (msg.content) {
            fields.push({ name: "Original Content", value: msg.content });
        }

        const embed = new EmbedBuilder().setTitle("Message deleted").setDescription("A message was deleted").addFields(fields).setColor("Red");

        await channel.send({ embeds: [embed] });
    }

    async onMessageEdit(before: Message | PartialMessage, after: Message | PartialMessage): Promise<void> {
        if (!after.guild) return;
        const selfMember = getSelfMember(after.guild);
        if (!selfMember) return;
        if (after.author?.id === selfMember.id) return;
        const channel = getLogChannel(after.guild);
        if (!channel) return;
        if (!channel.isTextBased()) return;
        if (!channel.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

        let fields: APIEmbedField[] = [];
        let files: AttachmentBuilder[] = [];

        fields.push({ name: "Author", value: after.author?.username ?? "Unknown" });

        if (before.content !== after.content) {
            if ((before.content?.length ?? 0) > 1000 || (after.content?.length ?? 0) > 1000) {
                files.push(new AttachmentBuilder(Buffer.from(before.content ?? "")).setName("before.txt"));
                files.push(new AttachmentBuilder(Buffer.from(after.content ?? "")).setName("after.txt"));
            } else {
                fields.push({
                    name: "Message content",
                    value: `${before.content} -> ${after.content}`
                });
            }
        }
        if (fields.length === 0) return;
        const embed = new EmbedBuilder().setTitle("Message edited").setDescription("A message was edited").addFields(fields).setColor("Yellow");
        if (!selfMember) return;
        await channel.send({
            embeds: [embed],
            files
        });
    }

    async onMemberJoin(member: GuildMember): Promise<void> {
        const selfMember = getSelfMember(member.guild);
        if (!selfMember) return;
        const channel = getLogChannel(member.guild);
        if (!channel) return;
        if (!channel.isTextBased()) return;
        if (!channel.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

        const embed = new EmbedBuilder().setTitle("Member joined").setDescription("A member joined the server").addFields({
            name: "Member name",
            value: member.user.username
        }, { name: "Member ID", value: member.id }).setColor("Green");
        if (!selfMember) return;
        await channel.send({ embeds: [embed] });
    }

    async onMemberEdit(before: GuildMember | PartialGuildMember, after: GuildMember | PartialGuildMember): Promise<void> {
        const selfMember = getSelfMember(after.guild);
        if (!selfMember) return;
        const channel = getLogChannel(after.guild);
        if (!channel) return;
        if (!channel.isTextBased()) return;
        if (!channel.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

        let fields: APIEmbedField[] = [];

        const update = await fetchAuditLog(after.guild, AuditLogEvent.MemberUpdate);

        fields.push({ name: "Editor", value: update });
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
        const embed = new EmbedBuilder().setTitle("Member edited").setDescription("A member was edited").addFields(fields).setColor("Yellow");

        await channel.send({ embeds: [embed] });
    }

    async onMemberLeave(member: GuildMember | PartialGuildMember): Promise<void> {
        const selfMember = getSelfMember(member.guild);
        if (!selfMember) return;
        const channel = getLogChannel(member.guild);
        if (!channel) return;
        if (!channel.isTextBased()) return;
        if (!channel.permissionsFor(selfMember)?.has(PermissionFlagsBits.SendMessages)) return;

        const embed = new EmbedBuilder().setTitle("Member left").setDescription("A member left the server").addFields({
            name: "Member name",
            value: member.user.username
        }, { name: "Member ID", value: member.id }).setColor("Red");
        await channel.send({ embeds: [embed] });
    }

    async onGuildAdd(guild: Guild): Promise<void> {
    }

    async onGuildRemove(guild: Guild): Promise<void> {
    }

    async onGuildEdit(before: Guild, after: Guild): Promise<void> {
        // check for: name change, icon change, inactive channel and time-out change, default notification settings
        const selfMember = getSelfMember(after);
        if (!selfMember) return;
        const channel = getLogChannel(after);
        if (!channel) return;
        if (!channel.isTextBased()) return;
        if (!channel.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

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
                value: `${before.afkChannelId ?? "*nothing*"} -> ${after.afkChannelId ?? "*nothing*"}`
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
        const embed = new EmbedBuilder().setTitle("Server edited").setDescription("The server was edited").addFields(fields).setColor("Yellow");
        await channel.send({ embeds: [embed] });
    }

    async onEmojiCreate(emoji: GuildEmoji): Promise<void> {
        if (!emoji.guild) return;
        const selfMember = getSelfMember(emoji.guild);
        if (!selfMember) return;
        const channel = getLogChannel(emoji.guild);
        if (!channel) return;
        if (!channel.isTextBased()) return;
        if (!channel.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

        let moderator = await fetchAuditLog(emoji.guild, AuditLogEvent.EmojiCreate);

        const embed = new EmbedBuilder()
            .setTitle("Emoji created")
            .setDescription("An emoji was created")
            .addFields({ name: "Emoji name", value: emoji.name ?? "unknown" }, {
                name: "Emoji ID",
                value: emoji.id
            }, { name: "Creator", value: moderator })
            .setColor("Green");
        await channel.send({ embeds: [embed] });
    }

    async onEmojiDelete(emoji: GuildEmoji): Promise<void> {
        if (!emoji.guild) return;
        const selfMember = getSelfMember(emoji.guild);
        if (!selfMember) return;
        const channel = getLogChannel(emoji.guild);
        if (!channel) return;
        if (!channel.isTextBased()) return;
        if (!channel.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

        let moderator = await fetchAuditLog(emoji.guild, AuditLogEvent.EmojiDelete);
        const embed = new EmbedBuilder()
            .setTitle("Emoji deleted")
            .setDescription("An emoji was deleted")
            .addFields({ name: "Emoji name", value: emoji.name ?? "unknown" }, {
                name: "Emoji ID",
                value: emoji.id
            }, { name: "Deleter", value: moderator })
            .setColor("Red");
        await channel.send({ embeds: [embed] });
    }

    async onEmojiEdit(before: GuildEmoji, after: GuildEmoji): Promise<void> {
        if (!after.guild) return;
        const selfMember = getSelfMember(after.guild);
        if (!selfMember) return;
        const logs = getLogChannel(after.guild);
        if (!logs) return;
        if (!logs.isTextBased()) return;
        if (!logs.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

        let moderator = await fetchAuditLog(after.guild, AuditLogEvent.EmojiUpdate);

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

        const embed = new EmbedBuilder().setTitle("Emoji edited").setDescription("An emoji was edited").addFields(fields).setColor("Yellow");
        await logs.send({ embeds: [embed] });
    }

    async onStickerCreate(sticker: Sticker): Promise<void> {
        if (!sticker.guild) return;
        const selfMember = getSelfMember(sticker.guild);
        if (!selfMember) return;
        const logs = getLogChannel(sticker.guild);
        if (!logs) return;
        if (!logs.isTextBased()) return;
        if (!logs.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

        let moderator = await fetchAuditLog(sticker.guild, AuditLogEvent.StickerCreate);

        const embed = new EmbedBuilder()
            .setTitle("Sticker created")
            .setDescription("A sticker was created")
            .addFields({ name: "Sticker name", value: sticker.name ?? "unknown" }, {
                name: "Sticker description",
                value: sticker.description ?? "unknown"
            }, { name: "Sticker ID", value: sticker.id }, { name: "Creator", value: moderator })
            .setColor("Green");
        await logs.send({ embeds: [embed] });
    }

    async onStickerDelete(sticker: Sticker): Promise<void> {
        if (!sticker.guild) return;
        const selfMember = getSelfMember(sticker.guild);
        if (!selfMember) return;
        const logs = getLogChannel(sticker.guild);
        if (!logs) return;
        if (!logs.isTextBased()) return;
        if (!logs.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

        let moderator = await fetchAuditLog(sticker.guild, AuditLogEvent.StickerDelete);

        const embed = new EmbedBuilder()
            .setTitle("Sticker deleted")
            .setDescription("A sticker was deleted")
            .addFields({ name: "Sticker name", value: sticker.name ?? "unknown" }, {
                name: "Sticker description",
                value: sticker.description ?? "unknown"
            }, { name: "Sticker ID", value: sticker.id }, { name: "Deleter", value: moderator })
            .setColor("Red");
        await logs.send({ embeds: [embed] });
    }

    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {
        if (!after.guild) return;
        const selfMember = getSelfMember(after.guild);
        if (!selfMember) return;
        const logs = getLogChannel(after.guild);
        if (!logs) return;
        if (!logs.isTextBased()) return;
        if (!logs.permissionsFor(selfMember).has(PermissionFlagsBits.SendMessages)) return;

        let moderator = await fetchAuditLog(after.guild, AuditLogEvent.StickerUpdate);
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

        const embed = new EmbedBuilder().setTitle("Sticker edited").setDescription("A sticker was edited").addFields(fields).setColor("Yellow");
        await logs.send({ embeds: [embed] });
    }
    async onTick(): Promise<void> {}
    async onReady(client: Client): Promise<void> {}
}
