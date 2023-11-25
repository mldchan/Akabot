import {
  ChatInputCommandInteraction,
  CacheType,
  ButtonInteraction,
  Role,
  Channel,
  Message,
  GuildMember,
  SlashCommandBuilder,
  PermissionsBitField,
} from "discord.js";
import { AllCommands, Module } from "./type";
import { getSetting, setSetting } from "../data/settings";

async function verifyTextableTextChannel(
  ch: Channel,
  int: ChatInputCommandInteraction<CacheType>,
  s: string
): Promise<boolean> {
  if (!int.guild) return false;
  if (!int.member) return false;
  if (!int.options) return false;
  const newChannelChannel = int.guild.channels.cache.get(ch.id);
  if (!newChannelChannel) {
    await int.reply({
      content: "Channel not found",
      ephemeral: true,
    });
    return false;
  }
  if (!newChannelChannel.isTextBased()) {
    await int.reply({
      content: "The channel has to be a text channel.",
      ephemeral: true,
    });
    return false;
  }
  if (
    !newChannelChannel.permissionsFor(s) ||
    newChannelChannel.permissionsFor(s) === null
  ) {
    await int.reply({
      content: "Could not verify permissions for the channel",
      ephemeral: true,
    });
    return false;
  }
  if (
    !newChannelChannel
      .permissionsFor(s)!
      .has(PermissionsBitField.Flags.SendMessages)
  ) {
    await int.reply({
      content: "The bot has to have permission to send messages",
      ephemeral: true,
    });
    return false;
  }

  return true;
}

async function handleLoggingSubcommands(
  interaction: ChatInputCommandInteraction<CacheType>,
  selfMemberId: string
) {
  if (!interaction.guild) return;
  if (!interaction.member) return;
  if (!interaction.options) return;
  const loggingGroup = interaction.options.getSubcommand();
  if (loggingGroup === "channel") {
    const newChannel = interaction.options.getChannel("channel");
    const currentChannel = getSetting(
      interaction.guild.id,
      "loggingChannel",
      ""
    );
    if (!newChannel) {
      if (currentChannel != "") {
        await interaction.reply({
          content: `The current logging channel is <#${currentChannel}>`,
          ephemeral: true,
        });
      } else {
        await interaction.reply({
          content: `There is no logging channel set`,
          ephemeral: true,
        });
      }
    } else {
      if (
        !(await verifyTextableTextChannel(
          newChannel as Channel,
          interaction,
          selfMemberId
        ))
      ) {
        return;
      }
      await interaction.reply({
        content: `The logging channel has been set to <#${newChannel.id}>`,
        ephemeral: true,
      });
      setSetting(interaction.guild.id, "loggingChannel", newChannel.id);
    }
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
    const newChannel = interaction.options.getChannel("channel");
    const currentChannel = getSetting(
      interaction.guild.id,
      "welcomeChannel",
      ""
    );
    if (!newChannel) {
      if (currentChannel != "") {
        await interaction.reply({
          content: `The current welcome channel is <#${currentChannel}>`,
          ephemeral: true,
        });
      } else {
        await interaction.reply({
          content: `There is no welcome channel set`,
          ephemeral: true,
        });
      }
    } else {
      if (
        !(await verifyTextableTextChannel(
          newChannel as Channel,
          interaction,
          selfMemberId
        ))
      ) {
        return;
      }
      await interaction.reply({
        content: `The welcome channel has been set to <#${newChannel.id}>`,
        ephemeral: true,
      });
      setSetting(interaction.guild.id, "welcomeChannel", newChannel.id);
    }
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
    const newChannel = interaction.options.getChannel("channel");
    const currentChannel = getSetting(
      interaction.guild.id,
      "goodbyeChannel",
      ""
    );
    if (!newChannel) {
      if (currentChannel != "") {
        await interaction.reply({
          content: `The current goodbye channel is <#${currentChannel}>`,
          ephemeral: true,
        });
      } else {
        await interaction.reply({
          content: `There is no goodbye channel set`,
          ephemeral: true,
        });
      }
    } else {
      if (
        !(await verifyTextableTextChannel(
          newChannel as Channel,
          interaction,
          selfMemberId
        ))
      ) {
        return;
      }
      await interaction.reply({
        content: `The goodbye channel has been set to <#${newChannel.id}>`,
        ephemeral: true,
      });
      setSetting(interaction.guild.id, "goodbyeChannel", newChannel.id);
    }
  }
}

export class SettingsModule implements Module {
  commands: AllCommands = [
    new SlashCommandBuilder()
      .setName("settings")
      .setDescription("Manage bot settings")
      .setDMPermission(false)
      .setDefaultMemberPermissions(PermissionsBitField.Flags.ManageGuild)
      .addSubcommandGroup((loggingGroup) =>
        loggingGroup
          .setName("logging")
          .setDescription("Manage logging settings")
          .addSubcommand((channel) =>
            channel
              .setName("channel")
              .setDescription("See what channel is set or change it")
              .addChannelOption((newChannelOption) =>
                newChannelOption
                  .setName("channel")
                  .setDescription("The new channel to set")
                  .setRequired(false)
              )
          )
      )
      .addSubcommandGroup((welcomeGroup) =>
        welcomeGroup
          .setName("welcome")
          .setDescription("Welcome new members")
          .addSubcommand((channel) =>
            channel
              .setName("channel")
              .setDescription("See what channel is set or change it")
              .addChannelOption((newChannelOption) =>
                newChannelOption
                  .setName("channel")
                  .setDescription("Set the channel to this")
                  .setRequired(false)
              )
          )
      )
      .addSubcommandGroup((goodbyeGroup) =>
        goodbyeGroup
          .setName("goodbye")
          .setDescription("Say goodbye to leaving members")
          .addSubcommand((channel) =>
            channel
              .setName("channel")
              .setDescription("See what channel is set or change it")
              .addChannelOption((newChannelOption) =>
                newChannelOption
                  .setName("channel")
                  .setDescription("Set the channel to this")
                  .setRequired(false)
              )
          )
          .addSubcommand((messageType) =>
            messageType
              .setName("type")
              .setDescription(
                "If you want to use an embed, or a normal message."
              )
              .addStringOption((newValue) =>
                newValue
                  .setName("type")
                  .setDescription("Change the message type")
                  .setChoices(
                    { name: "Embed", value: "embed" },
                    { name: "Normal message", value: "normal" }
                  )
              )
          )
          .addSubcommand((messageFormat) =>
            messageFormat
              .setName("format")
              .setDescription("Set the format")
              .addStringOption((newFormat) =>
                newFormat
                  .setName("format")
                  .setDescription("The new format to use")
                  .setMinLength(2)
              )
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
