import {
    ChatInputCommandInteraction,
    CacheType,
    ButtonInteraction,
    Role,
    Channel,
    Message,
    GuildMember,
    Guild,
    Emoji,
    Sticker,
    Client
} from "discord.js";
import { AllCommands, Module } from "./type";

export class TemplateModule implements Module {
    async onEmojiCreate(emoji: Emoji): Promise<void> {}
    async onEmojiDelete(emoji: Emoji): Promise<void> {}
    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {}
    async onStickerCreate(sticker: Sticker): Promise<void> {}
    async onStickerDelete(sticker: Sticker): Promise<void> {}
    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {}
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
    async onMemberJoin(member: GuildMember): Promise<void> {}
    async onMemberEdit(before: GuildMember, after: GuildMember): Promise<void> {}
    async onMemberLeave(member: GuildMember): Promise<void> {}
    async onGuildAdd(guild: Guild): Promise<void> {}
    async onGuildRemove(guild: Guild): Promise<void> {}
    async onGuildEdit(before: Guild, after: Guild): Promise<void> {}
    async onReady(client: Client): Promise<void> {}
}
