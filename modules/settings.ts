import {
  ChatInputCommandInteraction,
  CacheType,
  ButtonInteraction,
  Role,
  Channel,
  Message,
  GuildMember,
  PermissionsBitField,
} from "discord.js";
import { AllCommands, Module } from "./type";
import {
  ChannelSetting,
  SettingsCommandBuilder,
  SettingsGroupBuilder,
  StringSetting,
  setChannel,
} from "../types/settings";

async function handleLoggingSubcommands(
  interaction: ChatInputCommandInteraction<CacheType>,
  selfMemberId: string
) {
  if (!interaction.guild) return;
  if (!interaction.member) return;
  if (!interaction.options) return;
  const loggingGroup = interaction.options.getSubcommand();
  if (loggingGroup === "channel") {
    setChannel("logging", "loggingChannel", interaction, selfMemberId);
  }
}

async function handleWelcomeSubcommands(
  interaction: ChatInputCommandInteraction<CacheType>,
  selfMemberId: string
) {
  if (!interaction.guild) return;
  if (!interaction.member) return;
  if (!interaction.options) return;
  const group = interaction.options.getSubcommand();
  if (group === "channel") {
    setChannel("welcome", "welcomeChannel", interaction, selfMemberId);
  }
}
async function handleGoodbyeSubcommands(
  interaction: ChatInputCommandInteraction<CacheType>,
  selfMemberId: string
) {
  if (!interaction.guild) return;
  if (!interaction.member) return;
  if (!interaction.options) return;
  const group = interaction.options.getSubcommand();
  if (group === "channel") {
    setChannel("goodbye", "goodbyeChannel", interaction, selfMemberId);
  }
}

export class SettingsModule implements Module {
  commands: AllCommands = [
    new SettingsCommandBuilder()
      .addSettingsGroup(
        new SettingsGroupBuilder("logging").addChannelSetting(
          new ChannelSetting("channel")
        )
      )
      .addSettingsGroup(
        new SettingsGroupBuilder("welcome").addChannelSetting(
          new ChannelSetting("channel")
        )
      )
      .addSettingsGroup(
        new SettingsGroupBuilder("goodbye").addChannelSetting(
          new ChannelSetting("channel")
        )
      ),
  ];
  selfMemberId: string = "";
  async onSlashCommand(
    interaction: ChatInputCommandInteraction<CacheType>
  ): Promise<void> {
    if (interaction.commandName !== "settings") return;
    if (!interaction.guild) return;
    if (!interaction.member) return;
    if (!interaction.options) return;
    const member = interaction.member as GuildMember;
    if (
      !member.permissions.has(PermissionsBitField.Flags.ManageGuild) &&
      !member.permissions.has(PermissionsBitField.Flags.Administrator)
    ) {
      await interaction.reply({
        content: "You do not have permissions",
        ephemeral: true,
      });
      return;
    }

    const subcommand = interaction.options.getSubcommandGroup();
    if (subcommand === "logging") {
      await handleLoggingSubcommands(interaction, this.selfMemberId);
    }
    if (subcommand === "welcome") {
      await handleWelcomeSubcommands(interaction, this.selfMemberId);
    }
    if (subcommand === "goodbye") {
      await handleGoodbyeSubcommands(interaction, this.selfMemberId);
    }
  }
  async onButtonClick(
    interaction: ButtonInteraction<CacheType>
  ): Promise<void> {}
  async onRoleCreate(role: Role): Promise<void> {}
  async onRoleEdit(before: Role, after: Role): Promise<void> {}
  async onRoleDelete(role: Role): Promise<void> {}
  async onChannelCreate(role: Channel): Promise<void> {}
  async onChannelEdit(before: Channel, after: Channel): Promise<void> {}
  async onChannelDelete(role: Channel): Promise<void> {}
  async onMessage(msg: Message<boolean>): Promise<void> {}
  async onMessageDelete(msg: Message<boolean>): Promise<void> {}
  async onMessageEdit(
    before: Message<boolean>,
    after: Message<boolean>
  ): Promise<void> {}
  async onMemberJoin(member: GuildMember): Promise<void> {}
  async onMemberEdit(before: GuildMember, after: GuildMember): Promise<void> {}
  async onMemberLeave(member: GuildMember): Promise<void> {}
}
