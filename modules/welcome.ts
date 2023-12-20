import {
    ChatInputCommandInteraction,
    CacheType,
    ButtonInteraction,
    Role,
    Channel,
    Message,
    GuildMember,
    EmbedBuilder,
    Guild,
    Emoji,
    Sticker, Client
} from "discord.js";
import { AllCommands, Module } from "./type";
import { getSetting } from "../data/settings";
import { getSelfMember } from "../utilities/useful";

export class WelcomeModule implements Module {
    commands: AllCommands = [];
    selfMemberId: string = "";
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
    async onMemberJoin(member: GuildMember): Promise<void> {
        const channel = getSetting(member.guild.id, "welcomeChannel", "");
        if (channel === "") return;
        const channelRes = member.guild.channels.cache.get(channel);
        if (!channelRes) return;
        if (!channelRes.isTextBased()) return;

        const selfMember = getSelfMember(member.guild);
        if (!selfMember) return;
        if (!selfMember.permissionsIn(channelRes).has("SendMessages")) return;

        const memberNameType = getSetting(member.guild.id, "welcomeNameType", "nickname");
        const memberName = memberNameType === "nickname" ? member.user.displayName : member.user.username;
        const embed = new EmbedBuilder()
            .setTitle(`Welcome ${memberName}`)
            .setDescription(`Welcome to ${member.guild.name}, ${memberName}! Enjoy your stay.`)
            .setColor("Green");
        await channelRes.send({ embeds: [embed] });
    }
    async onMemberEdit(before: GuildMember, after: GuildMember): Promise<void> {}
    async onMemberLeave(member: GuildMember): Promise<void> {}
    async onGuildAdd(guild: Guild): Promise<void> {}
    async onGuildRemove(guild: Guild): Promise<void> {}
    async onGuildEdit(before: Guild, after: Guild): Promise<void> {}
    async onEmojiCreate(emoji: Emoji): Promise<void> {}
    async onEmojiDelete(emoji: Emoji): Promise<void> {}
    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {}
    async onStickerCreate(sticker: Sticker): Promise<void> {}
    async onStickerDelete(sticker: Sticker): Promise<void> {}
    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {}
    async onTick(): Promise<void> {}
    async onReady(client: Client): Promise<void> {
    }
}
