import { CacheType, Channel, ChatInputCommandInteraction, PermissionFlagsBits, PermissionsBitField, SlashCommandBuilder, SlashCommandSubcommandBuilder, SlashCommandSubcommandGroupBuilder } from "discord.js";
import { getSetting, setSetting } from "../data/settings";

export class SettingsCommandBuilder extends SlashCommandBuilder {
    constructor() {
        super();
        this.setName("settings").setDescription("Bot settings").setDMPermission(false).setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild);
    }

    addSettingsGroup(x: SettingsGroupBuilder): this {
        this.addSubcommandGroup(x);
        return this;
    }
}

export class SettingsGroupBuilder extends SlashCommandSubcommandGroupBuilder {
    constructor(group: string) {
        super();
        this.setName(group).setDescription(`Manage settings for ${group}`);
    }

    addStringSetting(string: StringSetting): this {
        this.addSubcommand(string);
        return this;
    }

    addChannelSetting(channel: ChannelSetting): this {
        this.addSubcommand(channel);
        return this;
    }
}

export class StringSetting extends SlashCommandSubcommandBuilder {
    constructor(name: string) {
        super();
        this.setName(name)
            .setDescription(`See what is ${name} set to or change it`)
            .addStringOption((newValue) => newValue.setName(name).setDescription(`Change ${name} to something different`));
    }
}

export class ChannelSetting extends SlashCommandSubcommandBuilder {
    constructor(name: string) {
        super();
        this.setName(name)
            .setDescription(`See what ${name} is set to or change it`)
            .addChannelOption((newValue) => newValue.setName(name).setDescription(`Change ${name} to something different`));
    }
}

// METHODS FOR QUICK SETTINGS MANAGEMENT
async function verifyTextableTextChannel(ch: Channel, int: ChatInputCommandInteraction<CacheType>, s: string): Promise<boolean> {
    if (!int.guild) return false;
    if (!int.member) return false;
    if (!int.options) return false;
    const newChannelChannel = int.guild.channels.cache.get(ch.id);
    if (!newChannelChannel) {
        await int.reply({
            content: "Channel not found",
            ephemeral: true
        });
        return false;
    }
    if (!newChannelChannel.isTextBased()) {
        await int.reply({
            content: "The channel has to be a text channel.",
            ephemeral: true
        });
        return false;
    }
    if (!newChannelChannel.permissionsFor(s) || newChannelChannel.permissionsFor(s) === null) {
        await int.reply({
            content: "Could not verify permissions for the channel",
            ephemeral: true
        });
        return false;
    }
    if (!newChannelChannel.permissionsFor(s)!.has(PermissionsBitField.Flags.SendMessages)) {
        await int.reply({
            content: "The bot has to have permission to send messages",
            ephemeral: true
        });
        return false;
    }

    return true;
}

export async function setChannel(channelName: string, key: string, interaction: ChatInputCommandInteraction<CacheType>, selfMemberId: string) {
    if (!interaction.guild) return;
    if (!interaction.member) return;
    if (!interaction.options) return;

    const newChannel = interaction.options.getChannel("channel");
    const currentChannel = getSetting(interaction.guild.id, key, "");
    if (!newChannel) {
        if (currentChannel != "") {
            await interaction.reply({
                content: `The current ${channelName} channel is <#${currentChannel}>`,
                ephemeral: true
            });
        } else {
            await interaction.reply({
                content: `There is no ${channelName} channel set`,
                ephemeral: true
            });
        }
    } else {
        if (!(await verifyTextableTextChannel(newChannel as Channel, interaction, selfMemberId))) {
            return;
        }
        await interaction.reply({
            content: `The ${channelName} channel has been set to <#${newChannel.id}>`,
            ephemeral: true
        });
        setSetting(interaction.guild.id, key, newChannel.id);
    }
}
