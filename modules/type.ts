import {
  ButtonInteraction,
  CacheType,
  Channel,
  ChatInputCommandInteraction,
  GuildMember,
  Message,
  PartialGuildMember,
  PartialMessage,
  Role,
  SlashCommandBuilder,
  SlashCommandSubcommandsOnlyBuilder,
} from "discord.js";

export type AllCommands =
  | SlashCommandBuilder[]
  | SlashCommandSubcommandsOnlyBuilder[];

export interface Module {
  commands: AllCommands;
  selfMemberId: string;
  onSlashCommand(
    interaction: ChatInputCommandInteraction<CacheType>
  ): Promise<void>;
  onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void>;

  onRoleCreate(role: Role): Promise<void>;
  onRoleEdit(before: Role, after: Role): Promise<void>;
  onRoleDelete(role: Role): Promise<void>;

  onChannelCreate(channel: Channel): Promise<void>;
  onChannelEdit(before: Channel, after: Channel): Promise<void>;
  onChannelDelete(channel: Channel): Promise<void>;

  onMessage(msg: Message): Promise<void>;
  onMessageDelete(msg: Message | PartialMessage): Promise<void>;
  onMessageEdit(
    before: Message | PartialMessage,
    after: Message | PartialMessage
  ): Promise<void>;

  onMemberJoin(member: GuildMember): Promise<void>;
  onMemberEdit(
    before: GuildMember | PartialGuildMember,
    after: GuildMember
  ): Promise<void>;
  onMemberLeave(member: GuildMember | PartialGuildMember): Promise<void>;
}
