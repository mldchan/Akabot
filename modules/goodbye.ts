import {
    AuditLogEvent,
    ButtonInteraction,
    CacheType,
    Channel,
    ChatInputCommandInteraction, Client,
    EmbedBuilder,
    Emoji,
    Guild,
    GuildMember,
    Message,
    Role,
    Sticker
} from "discord.js";
import { AllCommands, Module } from "@/modules/type";
import { getSetting } from "@/data/settings";
import { getSelfMember } from "@/utilities/useful";

export class GoodbyeModule implements Module {
    commands: AllCommands = [];
    selfMemberId: string = "";

    async onGuildAdd(guild: Guild): Promise<void> {
    }

    async onGuildRemove(guild: Guild): Promise<void> {
    }

    async onGuildEdit(before: Guild, after: Guild): Promise<void> {
    }

    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {
    }

    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {
    }

    async onRoleCreate(role: Role): Promise<void> {
    }

    async onRoleEdit(before: Role, after: Role): Promise<void> {
    }

    async onRoleDelete(role: Role): Promise<void> {
    }

    async onChannelCreate(role: Channel): Promise<void> {
    }

    async onChannelEdit(before: Channel, after: Channel): Promise<void> {
    }

    async onChannelDelete(role: Channel): Promise<void> {
    }

    async onMessage(msg: Message<boolean>): Promise<void> {
    }

    async onMessageDelete(msg: Message<boolean>): Promise<void> {
    }

    async onMessageEdit(before: Message<boolean>, after: Message<boolean>): Promise<void> {
    }

    async onMemberJoin(member: GuildMember): Promise<void> {
    }

    async onMemberEdit(before: GuildMember, after: GuildMember): Promise<void> {
    }

    async onMemberLeave(member: GuildMember): Promise<void> {
        const selfMember = getSelfMember(member.guild);
        if (!selfMember) return;
        const channel = getSetting(member.guild.id, "goodbyeChannel", "");
        if (channel === "") return;
        const channelRes = member.guild.channels.cache.get(channel);
        if (!channelRes) return;
        if (!channelRes.isTextBased()) return;
        if (!channelRes.permissionsFor(selfMember)?.has("SendMessages")) return;
        let reason: "leave" | "kick" | "ban" = "leave";
        if (selfMember.permissions.has("ViewAuditLog")) {
            const entry = (await member.guild.fetchAuditLogs({ limit: 1 })).entries.first();
            if (entry?.action === AuditLogEvent.MemberKick) reason = "kick";
            if (entry?.action === AuditLogEvent.MemberBanAdd) reason = "ban";
        }
        const embed = new EmbedBuilder();

        const memberNameType = getSetting(member.guild.id, "goodbyeNameType", "nickname");
        const memberName = memberNameType === "nickname" ? member.user.displayName : member.user.username;
        switch (reason) {
            case "leave":
                embed
                    .setTitle(`Goodbye ${memberName}`)
                    .setDescription(`We hope to see you later ${memberName}.`)
                    .setColor("Red");
                break;
            case "kick":
                embed.setTitle(`Goodbye ${memberName}`).setDescription(`${memberName} was kicked.`).setColor("Red");
                break;
            case "ban":
                embed.setTitle(`Goodbye ${memberName}`).setDescription(`${memberName} was banned.`).setColor("Red");
                break;
        }
        await channelRes.send({ embeds: [embed] });
    }

    async onEmojiCreate(emoji: Emoji): Promise<void> {
    }

    async onEmojiDelete(emoji: Emoji): Promise<void> {
    }

    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {
    }

    async onStickerCreate(sticker: Sticker): Promise<void> {
    }

    async onStickerDelete(sticker: Sticker): Promise<void> {
    }

    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {
    }
    async onReady(client: Client): Promise<void> {}
}
