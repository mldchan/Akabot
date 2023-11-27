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

type ViolationCountersMessageData = { messageIDs: string[] };
type ViolationCounters<T> = { serverId: string; eventId: string; violationsCount: number; expiryDate: Date; data?: T }[];

async function handleNoPfp(member: GuildMember) {
    const kickNoPfp = getSetting(member.guild.id, "AntiRaidNoPFP", "no");
    if (kickNoPfp !== "yes") return;
    if (member.user.avatar) return;

    try {
        await member.send("You have been kicked from a server for not having a profile picture. They have the bot set up like this.");
    } catch (_) {}

    let kickField = { name: "Action", value: "Kicked" };
    try {
        await member.kick("No PFP");
    } catch (_) {
        kickField = { name: "Action", value: "Failed to kick" };
    }

    const logChannelID = getSetting(member.guild.id, "loggingChannel", "");
    const logChannel = member.guild.channels.cache.get(logChannelID);
    if (!logChannel?.isTextBased()) return;

    const embed = new EmbedBuilder()
        .setTitle("A member is joining with no PFP in this Discord server")
        .addFields({ name: "Member", value: member.user.username }, kickField)
        .setColor("Red")
        .setTimestamp(new Date());

    await logChannel.send({ embeds: [embed] });
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
    } catch (_) {}

    let kickField = { name: "Action", value: "Kicked" };
    try {
        await member.kick("New account");
    } catch (_) {
        kickField = { name: "Action", value: "Failed to kick" };
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
                value: `${Math.floor((new Date().getTime() - member.user.createdAt.getTime()) / (24 * 60 * 60 * 1000))} days old`
            },
            { name: "Server setting", value: `${days} days old` }
        )
        .setColor("Red")
        .setTimestamp(new Date());

    await logChannel.send({ embeds: [embed] });
}

export class AntiRaidModule implements Module {
    violationCounters = [] as ViolationCounters<any>;
    vlNew(serverId: string, eventId: string, vlTime: number): number {
        this.violationCounters = this.violationCounters.filter((vl) => vl.expiryDate > new Date());
        const vl = this.violationCounters.find((vl) => vl.serverId === serverId && vl.eventId === eventId);
        if (vl) {
            vl.violationsCount++;
            vl.expiryDate = new Date(new Date().getTime() + vlTime);
            return vl.violationsCount;
        }
        this.violationCounters.push({
            serverId,
            eventId,
            violationsCount: 1,
            expiryDate: new Date(new Date().getTime() + vlTime)
        });
        return 1;
    }
    vlGetExtraData<T>(serverId: string, eventId: string): T | undefined {
        const vl = this.violationCounters.find((vl) => vl.serverId === serverId && vl.eventId === eventId);
        if (!vl) return undefined;
        return vl.data as T;
    }
    vlSetExtraData<T>(serverId: string, eventId: string, extraData: T): void {
        const vl = this.violationCounters.find((vl) => vl.serverId === serverId && vl.eventId === eventId);
        if (!vl) return;
        vl.data = extraData;
    }
    vlDelete(serverId: string, eventId: string): void {
        this.violationCounters = this.violationCounters.filter((vl) => vl.serverId !== serverId && vl.eventId !== eventId);
    }
    async onEmojiCreate(emoji: GuildEmoji): Promise<void> {}
    async onEmojiDelete(emoji: GuildEmoji): Promise<void> {
        const vl = this.vlNew(emoji.guild.id, "emojiDel", 3000);
        if (vl > 2) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await emoji.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.EmojiDelete })).entries.first()?.executor?.username ??
                    "Unknown";
            } catch (_) {}

            const logChannelID = getSetting(emoji.guild.id, "loggingChannel", "");
            const logChannel = emoji.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is mass deleting emojis in this Discord server")
                    .addFields({ name: "Deleter", value: auditLogs })
                    .setColor("Red")
                    .setTimestamp(new Date());
                await logChannel.send({ embeds: [embed] });
            }
            this.vlDelete(emoji.guild.id, "message");
        }

        const vl2 = this.vlNew(emoji.guild.id, "emojiDel2", 30000);
        if (vl2 > 5) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await emoji.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.EmojiDelete })).entries.first()?.executor?.username ??
                    "Unknown";
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
            this.vlDelete(emoji.guild.id, "message");
        }
    }
    async onEmojiEdit(before: GuildEmoji, after: GuildEmoji): Promise<void> {}
    async onStickerCreate(sticker: Sticker): Promise<void> {}
    async onStickerDelete(sticker: Sticker): Promise<void> {
        if (!sticker.guild) return;
        const vl = this.vlNew(sticker.guild.id, "stickerDel", 3000);
        if (vl > 2) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await sticker.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.StickerDelete })).entries.first()?.executor
                        ?.username ?? "Unknown";
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
            this.vlDelete(sticker.guild.id, "message");
        }
        const vl2 = this.vlNew(sticker.guild.id, "stickerDel2", 30000);
        if (vl2 > 5) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await sticker.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.StickerDelete })).entries.first()?.executor
                        ?.username ?? "Unknown";
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
            this.vlDelete(sticker.guild.id, "message");
        }
    }
    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {}
    commands: AllCommands = [];
    selfMemberId: string = "";
    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {}
    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {}
    async onRoleCreate(role: Role): Promise<void> {
        const vl = this.vlNew(role.guild.id, "roleCre", 3000);
        if (vl > 2) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await role.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.RoleCreate })).entries.first()?.executor?.username ??
                    "Unknown";
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
            this.vlDelete(role.guild.id, "message");
        }
        const vl2 = this.vlNew(role.guild.id, "roleCre2", 30000);
        if (vl2 > 5) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await role.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.RoleCreate })).entries.first()?.executor?.username ??
                    "Unknown";
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
            this.vlDelete(role.guild.id, "message");
        }
    }
    async onRoleEdit(before: Role, after: Role): Promise<void> {}
    async onRoleDelete(role: Role): Promise<void> {
        const vl = this.vlNew(role.guild.id, "roleDel", 3000);
        if (vl > 2) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await role.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.RoleDelete })).entries.first()?.executor?.username ??
                    "Unknown";
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
            this.vlDelete(role.guild.id, "message");
        }
        const vl2 = this.vlNew(role.guild.id, "roleDel2", 30000);
        if (vl2 > 5) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await role.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.RoleDelete })).entries.first()?.executor?.username ??
                    "Unknown";
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
            this.vlDelete(role.guild.id, "message");
        }
    }
    async onChannelCreate(channel: Channel): Promise<void> {
        if (channel.isDMBased()) return;
        if (!channel.guild) return;
        const vl = this.vlNew(channel.guild.id, "channelCre", 3000);
        if (vl > 2) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await channel.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.ChannelCreate })).entries.first()?.executor
                        ?.username ?? "Unknown";
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
            this.vlDelete(channel.guild.id, "message");
        }
        const vl2 = this.vlNew(channel.guild.id, "channelCre2", 30000);
        if (vl2 > 5) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await channel.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.ChannelCreate })).entries.first()?.executor
                        ?.username ?? "Unknown";
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
            this.vlDelete(channel.guild.id, "message");
        }
    }
    async onChannelEdit(before: Channel, after: Channel): Promise<void> {}
    async onChannelDelete(channel: Channel): Promise<void> {
        if (channel.isDMBased()) return;
        if (!channel.guild) return;
        const vl = this.vlNew(channel.guild.id, "channelDel", 3000);
        if (vl > 2) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await channel.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.ChannelDelete })).entries.first()?.executor
                        ?.username ?? "Unknown";
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
            this.vlDelete(channel.guild.id, "message");
        }
        const vl2 = this.vlNew(channel.guild.id, "channelDel2", 30000);
        if (vl2 > 5) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await channel.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.ChannelDelete })).entries.first()?.executor
                        ?.username ?? "Unknown";
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
            this.vlDelete(channel.guild.id, "message");
        }
    }
    async onMessage(msg: Message<boolean>): Promise<void> {
        if (!msg.guild) return;
        if (msg.author.bot) return;
        const vl = this.vlNew(msg.guild.id, `message${msg.author.id}`, 3000);
        let extraData = this.vlGetExtraData<ViolationCountersMessageData>(msg.guild.id, `message${msg.author.id}`) ?? { messageIDs: [] };
        extraData.messageIDs.push(msg.id);
        this.vlSetExtraData(msg.guild.id, `message${msg.author.id}`, extraData);

        if (vl > 4) {
            const spamSendAlert = getSetting(msg.guild.id, "AntiRaidSpamSendAlert", "no");
            if (spamSendAlert === "yes") {
                await msg.channel.send(`<@${msg.author.id}>, You are sending messages too fast!`);
            }
            const fields: { name: string; value: string }[] = [];
            const spamDeleteSetting = getSetting(msg.guild.id, "AntiRaidSpamDelete", "no");
            if (spamDeleteSetting === "yes" && msg.channel.isTextBased() && !msg.channel.isDMBased()) {
                try {
                    await msg.channel.bulkDelete(extraData.messageIDs);
                } catch (_) {
                    fields.push({ name: "Bulk delete", value: "Failed to bulk delete messages" });
                }
            } else {
                fields.push({ name: "Bulk delete", value: "Disabled" });
            }
            let timeoutStatus = { name: "Timeout", value: "10 seconds" };
            const spamTimeoutSetting = getSetting(msg.guild.id, "AntiRaidSpamTimeout", "no");
            if (spamTimeoutSetting === "yes") {
                try {
                    await msg.member?.timeout(10000, "Sending messages too fast!");
                } catch (_) {
                    timeoutStatus = { name: "Timeout", value: "Failed to timeout" };
                }
            } else {
                timeoutStatus = { name: "Timeout", value: "Disabled" };
            }
            const logChannelID = getSetting(msg.guild.id, "loggingChannel", "");
            const logChannel = msg.guild.channels.cache.get(logChannelID);
            if (logChannel?.isTextBased()) {
                const embed = new EmbedBuilder()
                    .setTitle("A member is spamming in this Discord server")
                    .addFields(
                        { name: "Member", value: msg.author.username },
                        { name: "Jump to latest message", value: `[Click here](${msg.url})` },
                        timeoutStatus,
                        ...fields
                    )
                    .setColor("Red")
                    .setTimestamp(new Date());
                await logChannel.send({ embeds: [embed] });
            }
            this.vlDelete(msg.guild.id, "message");
        }
    }
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
        const vl = this.vlNew(after.guild.id, "memberEdit", 3000);
        if (vl > 4) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await after.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.MemberUpdate })).entries.first()?.executor
                        ?.username ?? "Unknown";
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
            this.vlDelete(after.guild.id, "message");
        }
        const vl2 = this.vlNew(after.guild.id, "memberEdit", 30000);
        if (vl2 > 8) {
            let auditLogs = "Unknown (No Audit Logs permission)";
            try {
                auditLogs =
                    (await after.guild.fetchAuditLogs({ limit: 1, type: AuditLogEvent.MemberUpdate })).entries.first()?.executor
                        ?.username ?? "Unknown";
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
            this.vlDelete(after.guild.id, "message");
        }
    }
    async onMemberLeave(member: GuildMember): Promise<void> {}
    async onGuildAdd(guild: Guild): Promise<void> {}
    async onGuildRemove(guild: Guild): Promise<void> {}
    async onGuildEdit(before: Guild, after: Guild): Promise<void> {}
}
