import {
    ChatInputCommandInteraction,
    CacheType,
    ButtonInteraction,
    Role,
    Channel,
    Message,
    GuildMember,
    Guild,
    Sticker,
    EmbedBuilder,
    GuildEmoji,
    AuditLogEvent
} from "discord.js";
import { AllCommands, Module } from "./type";
import { getSetting } from "../data/settings";
import { ViolationCounters } from "../utilities/violationCounters";

async function handleNoPfp(member: GuildMember) {
    const kickNoPfp = getSetting(member.guild.id, "AntiRaidNoPFP", "no");
    if (kickNoPfp !== "yes") return;
    if (member.user.avatar) return;

    console.log("antiRaid", "handleNoPfp", member.user.username, member.user.avatar, "no pfp");
    try {
        await member.send(
            "You have been kicked from a server for not having a profile picture. They have the bot set up like this."
        );
        console.log("antiRaid", "handleNoPfp", member.user.username, "sent DM");
    } catch (_) {
        console.log("antiRaid", "handleNoPfp", member.user.username, "failed to send DM");
    }

    let kickField = { name: "Action", value: "Kicked" };
    try {
        await member.kick("No PFP");
        console.log("antiRaid", "handleNoPfp", member.user.username, "kicked");
    } catch (_) {
        kickField = { name: "Action", value: "Failed to kick" };
        console.log("antiRaid", "handleNoPfp", member.user.username, "failed to kick");
    }

    const logChannelID = getSetting(member.guild.id, "loggingChannel", "");
    const logChannel = member.guild.channels.cache.get(logChannelID);
    if (!logChannel?.isTextBased()) return;

    const embed = new EmbedBuilder()
        .setTitle("A member is joining with no PFP in this Discord server")
        .addFields({ name: "Member", value: member.user.username }, kickField)
        .setColor("Red")
        .setTimestamp(new Date());

    try {
        await logChannel.send({ embeds: [embed] });
        console.log("antiRaid", "handleNoPfp", member.user.username, "sent log message");
    } catch (_) {
        console.log("antiRaid", "handleNoPfp", member.user.username, "failed to send log message");
    }
}

async function handleNewAccount(member: GuildMember) {
    const kickNewAccounts = getSetting(member.guild.id, "AntiRaidNewMembers", "0");
    if (kickNewAccounts === "0" || isNaN(Number(kickNewAccounts))) return;
    const days = Number(kickNewAccounts);
    const daysAgo = new Date(new Date().getTime() - days * 24 * 60 * 60 * 1000);
    if (member.user.createdAt < daysAgo) return;

    try {
        await member.send(
            `Your account needs to be at least ${days} days old to join this server. Your account is ${Math.floor(
                (new Date().getTime() - member.user.createdAt.getTime()) / (24 * 60 * 60 * 1000)
            )} days old.`
        );
        console.log("antiRaid", "handleNewAccount", member.user.username, "sent DM");
    } catch (_) {
        console.log("antiRaid", "handleNewAccount", member.user.username, "failed to send DM");
    }

    let kickField = { name: "Action", value: "Kicked" };
    try {
        await member.kick("New account");
        console.log("antiRaid", "handleNewAccount", member.user.username, "kicked");
    } catch (_) {
        kickField = { name: "Action", value: "Failed to kick" };
        console.log("antiRaid", "handleNewAccount", member.user.username, "failed to kick");
    }

    const logChannelID = getSetting(member.guild.id, "loggingChannel", "");
    const logChannel = member.guild.channels.cache.get(logChannelID);
    if (!logChannel?.isTextBased()) return;

    const embed = new EmbedBuilder()
        .setTitle("A member is joining with a new account in this Discord server")
        .addFields(
            { name: "Member", value: member.user.username },
            kickField,
            {
                name: "Account age",
                value: `${Math.floor(
                    (new Date().getTime() - member.user.createdAt.getTime()) / (24 * 60 * 60 * 1000)
                )} days old`
            },
            { name: "Server setting", value: `${days} days old` }
        )
        .setColor("Red")
        .setTimestamp(new Date());

    try {
        await logChannel.send({ embeds: [embed] });
        console.log("antiRaid", "handleNewAccount", member.user.username, "sent log message");
    } catch (_) {
        console.log("antiRaid", "handleNewAccount", member.user.username, "failed to send log message");
    }
}

export class AntiRaidModule implements Module {
    violationCounters = new ViolationCounters();
    async onEmojiCreate(emoji: GuildEmoji): Promise<void> {}
    async onEmojiDelete(emoji: GuildEmoji): Promise<void> {
        const vl = this.violationCounters.vlNew(emoji.guild.id, "emojiDel", 3000);
        if (vl > 2) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await emoji.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.EmojiDelete })).entries.first()
                        ?.executor?.username ?? "Unknown";
            } catch (_) {}

            const logChannelID = getSetting(emoji.guild.id, "loggingChannel", "");
            const logChannel = emoji.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is mass deleting emojis in this Discord server")
                    .addFields({ name: "Deleter", value: auditLogs })
                    .setColor("Red")
                    .setTimestamp(new Date());
                try {
                    await logChannel.send({ embeds: [embed] });
                    console.log("antiRaid", "onEmojiDelete", emoji.guild.id, "sent log message");
                } catch (_) {
                    console.log("antiRaid", "onEmojiDelete", emoji.guild.id, "failed to send log message");
                }
            }
            this.violationCounters.vlDelete(emoji.guild.id, "message");
        }

        const vl2 = this.violationCounters.vlNew(emoji.guild.id, "emojiDel2", 30000);
        if (vl2 > 5) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await emoji.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.EmojiDelete })).entries.first()
                        ?.executor?.username ?? "Unknown";
            } catch (_) {}

            const logChannelID = getSetting(emoji.guild.id, "loggingChannel", "");
            const logChannel = emoji.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is mass deleting emojis over a longer period of time in this Discord server")
                    .addFields({ name: "Deleter", value: auditLogs })
                    .setColor("Red")
                    .setTimestamp(new Date());
                await logChannel.send({ embeds: [embed] });
            }
            this.violationCounters.vlDelete(emoji.guild.id, "message");
        }
    }
    async onEmojiEdit(before: GuildEmoji, after: GuildEmoji): Promise<void> {}
    async onStickerCreate(sticker: Sticker): Promise<void> {}
    async onStickerDelete(sticker: Sticker): Promise<void> {
        if (!sticker.guild) return;
        const vl = this.violationCounters.vlNew(sticker.guild.id, "stickerDel", 3000);
        if (vl > 2) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (
                        await sticker.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.StickerDelete })
                    ).entries.first()?.executor?.username ?? "Unknown";
            } catch (_) {}

            const logChannelID = getSetting(sticker.guild.id, "loggingChannel", "");
            const logChannel = sticker.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is mass deleting stickers in this Discord server")
                    .addFields({ name: "Deleter", value: auditLogs })
                    .setColor("Red")
                    .setTimestamp(new Date());
                await logChannel.send({ embeds: [embed] });
            }
            this.violationCounters.vlDelete(sticker.guild.id, "message");
        }
        const vl2 = this.violationCounters.vlNew(sticker.guild.id, "stickerDel2", 30000);
        if (vl2 > 5) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (
                        await sticker.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.StickerDelete })
                    ).entries.first()?.executor?.username ?? "Unknown";
            } catch (_) {}

            const logChannelID = getSetting(sticker.guild.id, "loggingChannel", "");
            const logChannel = sticker.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is mass deleting stickers over a longer period of time in this Discord server")
                    .addFields({ name: "Deleter", value: auditLogs })
                    .setColor("Red")
                    .setTimestamp(new Date());
                await logChannel.send({ embeds: [embed] });
            }
            this.violationCounters.vlDelete(sticker.guild.id, "message");
        }
    }
    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {}
    commands: AllCommands = [];
    selfMemberId: string = "";
    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {}
    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {}
    async onRoleCreate(role: Role): Promise<void> {
        const vl = this.violationCounters.vlNew(role.guild.id, "roleCre", 3000);
        if (vl > 2) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await role.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.RoleCreate })).entries.first()
                        ?.executor?.username ?? "Unknown";
            } catch (_) {}

            const logChannelID = getSetting(role.guild.id, "loggingChannel", "");
            const logChannel = role.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is mass creating roles in this Discord server")
                    .addFields({ name: "Creator", value: auditLogs })
                    .setColor("Red")
                    .setTimestamp(new Date());
                await logChannel.send({ embeds: [embed] });
            }
            this.violationCounters.vlDelete(role.guild.id, "message");
        }
        const vl2 = this.violationCounters.vlNew(role.guild.id, "roleCre2", 30000);
        if (vl2 > 5) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await role.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.RoleCreate })).entries.first()
                        ?.executor?.username ?? "Unknown";
            } catch (_) {}

            const logChannelID = getSetting(role.guild.id, "loggingChannel", "");
            const logChannel = role.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is mass creating roles over a longer period of time in this Discord server")
                    .addFields({ name: "Creator", value: auditLogs })
                    .setColor("Red")
                    .setTimestamp(new Date());
                await logChannel.send({ embeds: [embed] });
            }
            this.violationCounters.vlDelete(role.guild.id, "message");
        }
    }
    async onRoleEdit(before: Role, after: Role): Promise<void> {}
    async onRoleDelete(role: Role): Promise<void> {
        const vl = this.violationCounters.vlNew(role.guild.id, "roleDel", 3000);
        if (vl > 2) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await role.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.RoleDelete })).entries.first()
                        ?.executor?.username ?? "Unknown";
            } catch (_) {}

            const logChannelID = getSetting(role.guild.id, "loggingChannel", "");
            const logChannel = role.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is mass deleting roles in this Discord server")
                    .addFields({ name: "Deleter", value: auditLogs })
                    .setColor("Red")
                    .setTimestamp(new Date());
                await logChannel.send({ embeds: [embed] });
            }
            this.violationCounters.vlDelete(role.guild.id, "message");
        }
        const vl2 = this.violationCounters.vlNew(role.guild.id, "roleDel2", 30000);
        if (vl2 > 5) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await role.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.RoleDelete })).entries.first()
                        ?.executor?.username ?? "Unknown";
            } catch (_) {}

            const logChannelID = getSetting(role.guild.id, "loggingChannel", "");
            const logChannel = role.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is mass deleting roles over a longer period of time in this Discord server")
                    .addFields({ name: "Deleter", value: auditLogs })
                    .setColor("Red")
                    .setTimestamp(new Date());
                await logChannel.send({ embeds: [embed] });
            }
            this.violationCounters.vlDelete(role.guild.id, "message");
        }
    }
    async onChannelCreate(channel: Channel): Promise<void> {
        if (channel.isDMBased()) return;
        if (!channel.guild) return;
        const vl = this.violationCounters.vlNew(channel.guild.id, "channelCre", 3000);
        if (vl > 2) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (
                        await channel.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.ChannelCreate })
                    ).entries.first()?.executor?.username ?? "Unknown";
            } catch (_) {}

            const logChannelID = getSetting(channel.guild.id, "loggingChannel", "");
            const logChannel = channel.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is mass creating channels in this Discord server")
                    .addFields({ name: "Creator", value: auditLogs })
                    .setColor("Red")
                    .setTimestamp(new Date());
                await logChannel.send({ embeds: [embed] });
            }
            this.violationCounters.vlDelete(channel.guild.id, "message");
        }
        const vl2 = this.violationCounters.vlNew(channel.guild.id, "channelCre2", 30000);
        if (vl2 > 5) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (
                        await channel.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.ChannelCreate })
                    ).entries.first()?.executor?.username ?? "Unknown";
            } catch (_) {}

            const logChannelID = getSetting(channel.guild.id, "loggingChannel", "");
            const logChannel = channel.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is mass creating channels over a longer period of time in this Discord server")
                    .addFields({ name: "Creator", value: auditLogs })
                    .setColor("Red")
                    .setTimestamp(new Date());
                await logChannel.send({ embeds: [embed] });
            }
            this.violationCounters.vlDelete(channel.guild.id, "message");
        }
    }
    async onChannelEdit(before: Channel, after: Channel): Promise<void> {}
    async onChannelDelete(channel: Channel): Promise<void> {
        if (channel.isDMBased()) return;
        if (!channel.guild) return;
        const vl = this.violationCounters.vlNew(channel.guild.id, "channelDel", 3000);
        if (vl > 2) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (
                        await channel.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.ChannelDelete })
                    ).entries.first()?.executor?.username ?? "Unknown";
            } catch (_) {}

            const logChannelID = getSetting(channel.guild.id, "loggingChannel", "");
            const logChannel = channel.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is mass deleting channels in this Discord server")
                    .addFields({ name: "Deleter", value: auditLogs })
                    .setColor("Red")
                    .setTimestamp(new Date());
                await logChannel.send({ embeds: [embed] });
            }
            this.violationCounters.vlDelete(channel.guild.id, "message");
        }
        const vl2 = this.violationCounters.vlNew(channel.guild.id, "channelDel2", 30000);
        if (vl2 > 5) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (
                        await channel.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.ChannelDelete })
                    ).entries.first()?.executor?.username ?? "Unknown";
            } catch (_) {}

            const logChannelID = getSetting(channel.guild.id, "loggingChannel", "");
            const logChannel = channel.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is mass deleting channels over a longer period of time in this Discord server")
                    .addFields({ name: "Deleter", value: auditLogs })
                    .setColor("Red")
                    .setTimestamp(new Date());
                await logChannel.send({ embeds: [embed] });
            }
            this.violationCounters.vlDelete(channel.guild.id, "message");
        }
    }
    async onMessage(msg: Message<boolean>): Promise<void> {}
    async onMessageDelete(msg: Message<boolean>): Promise<void> {}
    async onMessageEdit(before: Message<boolean>, after: Message<boolean>): Promise<void> {}
    async onMemberJoin(member: GuildMember): Promise<void> {
        await handleNoPfp(member);
        await handleNewAccount(member);
    }
    async onMemberEdit(before: GuildMember, after: GuildMember): Promise<void> {
        if (!before.guild) return;
        if (!after.guild) return;
        if (before.nickname === after.nickname) return;
        const vl = this.violationCounters.vlNew(after.guild.id, "memberEdit", 3000);
        if (vl > 4) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await after.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.MemberUpdate })).entries.first()
                        ?.executor?.username ?? "Unknown";
            } catch (_) {}

            const logChannelID = getSetting(after.guild.id, "loggingChannel", "");
            const logChannel = after.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is mass changing nicknames in this Discord server")
                    .addFields({ name: "Changer", value: auditLogs })
                    .setColor("Red")
                    .setTimestamp(new Date());
                await logChannel.send({ embeds: [embed] });
            }
            this.violationCounters.vlDelete(after.guild.id, "message");
        }
        const vl2 = this.violationCounters.vlNew(after.guild.id, "memberEdit", 30000);
        if (vl2 > 8) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await after.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.MemberUpdate })).entries.first()
                        ?.executor?.username ?? "Unknown";
            } catch (_) {}

            const logChannelID = getSetting(after.guild.id, "loggingChannel", "");
            const logChannel = after.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is mass changing nicknames over a longer period of time in this Discord server")
                    .addFields({ name: "Changer", value: auditLogs })
                    .setColor("Red")
                    .setTimestamp(new Date());
                await logChannel.send({ embeds: [embed] });
            }
            this.violationCounters.vlDelete(after.guild.id, "message");
        }
    }
    async onMemberLeave(member: GuildMember): Promise<void> {}
    async onGuildAdd(guild: Guild): Promise<void> {}
    async onGuildRemove(guild: Guild): Promise<void> {}
    async onGuildEdit(before: Guild, after: Guild): Promise<void> {}
}
