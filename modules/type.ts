import {
  ButtonInteraction,
  CacheType,
  Channel,
  ChatInputCommandInteraction,
  GuildMember,
  Message,
  Role,
  SlashCommandBuilder,
  SlashCommandSubcommandsOnlyBuilder,
} from "discord.js";

export type AllCommands =
  | SlashCommandBuilder[]
  | SlashCommandSubcommandsOnlyBuilder[];

export interface Module {
  commands: AllCommands;
  onSlashCommand(
    interaction: ChatInputCommandInteraction<CacheType>
  ): Promise<void>;
  onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void>;

  onRoleCreate(role: Role): Promise<void>;
  onRoleEdit(before: Role, after: Role): Promise<void>;
  onRoleDelete(role: Role): Promise<void>;

  onChannelCreate(role: Channel): Promise<void>;
  onChannelEdit(before: Channel, after: Channel): Promise<void>;
  onChannelDelete(role: Channel): Promise<void>;

  onMessage(msg: Message): Promise<void>;
  onMessageDelete(msg: Message): Promise<void>;
  onMessageEdit(before: Message, after: Message): Promise<void>;

  onMemberJoin(member: GuildMember): Promise<void>;
  onMemberEdit(before: GuildMember, after: GuildMember): Promise<void>;
  onMemberLeave(member: GuildMember): Promise<void>;
}
