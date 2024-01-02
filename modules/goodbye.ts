import {
    AuditLogEvent,
    ButtonInteraction,
    CacheType,
    Channel,
    ChatInputCommandInteraction,
    Client,
    EmbedBuilder,
    Emoji,
    Guild,
    GuildMember,
    Message,
    Role,
    Sticker
} from "discord.js";
import { AllCommands, Module } from "./type";
import { getSetting } from "../data/settings";
import { getSelfMember } from "../utilities/useful";

export class GoodbyeModule implements Module {
    commands: AllCommands = [];
    selfMemberId: string = "";

    async onGuildAdd(guild: Guild): Promise<void> {}

    async onGuildRemove(guild: Guild): Promise<void> {}

    async onGuildEdit(before: Guild, after: Guild): Promise<void> {}

    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {}

    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {}

    async onRoleCreate(role: Role): Promise<void> {}

    async onRoleEdit(before: Role, after: Role): Promise<void> {}

    async onRoleDelete(role: Role): Promise<void> {}

    async onChannelCreate(role: Channel): Promise<void> {}

    async onChannelEdit(before: Channel, after: Channel): Promise<void> {}

    async onChannelDelete(role: Channel): Promise<void> {}

    async onMessage(msg: Message<boolean>): Promise<void> {}

    async onMessageDelete(msg: Message<boolean>): Promise<void> {}

    async onMessageEdit(before: Message<boolean>, after: Message<boolean>): Promise<void> {}

    async onMemberJoin(member: GuildMember): Promise<void> {}

    async onMemberEdit(before: GuildMember, after: GuildMember): Promise<void> {}

    async onMemberLeave(member: GuildMember): Promise<void> {
        const selfMember = getSelfMember(member.guild);
        if (!selfMember) return;
        const channel = getSetting(member.guild.id, "goodbyeChannel", "");
        if (channel === "") return;
        const channelRes = member.guild.channels.cache.get(channel);
        if (!channelRes) return;
        if (!channelRes.isTextBased()) return;
        if (!channelRes.permissionsFor(selfMember)?.has("SendMessages")) return;
        let way: "leave" | "kick" | "ban" = "leave";
        let reason = "";
        if (selfMember.permissions.has("ViewAuditLog")) {
            const entry = (await member.guild.fetchAuditLogs({ limit: 1 })).entries.first();
            if (entry?.action === AuditLogEvent.MemberKick) {
                way = "kick";
                reason = entry.reason ?? "";
            }
            if (entry?.action === AuditLogEvent.MemberBanAdd) {
                way = "ban";
                reason = entry.reason ?? "";
            }
        }
        const embed = new EmbedBuilder();

        const memberNameType = getSetting(member.guild.id, "goodbyeNameType", "nickname");
        const memberName = memberNameType === "nickname" ? member.user.displayName : member.user.username;

        let goodbyeTitle = getSetting(member.guild.id, "goodbyeTitle", "Goodbye");
        goodbyeTitle = goodbyeTitle.replace("{user}", memberName);
        goodbyeTitle = goodbyeTitle.replace("{server}", member.guild.name);
        goodbyeTitle = goodbyeTitle.replace("{memberCount}", member.guild.memberCount.toString());

        let goodbyeMessage = getSetting(member.guild.id, "goodbyeMessage", "Goodbye {user} :(");
        goodbyeMessage = goodbyeMessage.replace("{user}", memberName);
        goodbyeMessage = goodbyeMessage.replace("{server}", member.guild.name);
        goodbyeMessage = goodbyeMessage.replace("{memberCount}", member.guild.memberCount.toString());

        let goodbyeMessageKick = getSetting(member.guild.id, "goodbyeMessageKick", "{user} was kicked");
        goodbyeMessageKick = goodbyeMessageKick.replace("{user}", memberName);
        goodbyeMessageKick = goodbyeMessageKick.replace("{reason}", reason);
        goodbyeMessageKick = goodbyeMessageKick.replace("{server}", member.guild.name);
        goodbyeMessageKick = goodbyeMessageKick.replace("{memberCount}", member.guild.memberCount.toString());

        let goodbyeMessageBan = getSetting(member.guild.id, "goodbyeMessageBan", "{user} was banned");
        goodbyeMessageBan = goodbyeMessageBan.replace("{user}", memberName);
        goodbyeMessageBan = goodbyeMessageBan.replace("{reason}", reason);
        goodbyeMessageBan = goodbyeMessageBan.replace("{server}", member.guild.name);
        goodbyeMessageBan = goodbyeMessageBan.replace("{memberCount}", member.guild.memberCount.toString());

        switch (way) {
            case "leave":
                embed.setTitle(goodbyeTitle).setDescription(goodbyeMessage).setColor("Red");
                break;
            case "kick":
                embed.setTitle(goodbyeTitle).setDescription(goodbyeMessageKick).setColor("Red");
                break;
            case "ban":
                embed.setTitle(goodbyeTitle).setDescription(goodbyeMessageBan).setColor("Red");
                break;
        }
        await channelRes.send({ embeds: [embed] });
    }

    async onEmojiCreate(emoji: Emoji): Promise<void> {}

    async onEmojiDelete(emoji: Emoji): Promise<void> {}

    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {}

    async onStickerCreate(sticker: Sticker): Promise<void> {}

    async onStickerDelete(sticker: Sticker): Promise<void> {}

    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {}
    async onReady(client: Client): Promise<void> {}
}
