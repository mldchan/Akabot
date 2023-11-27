import {
    APIApplicationCommandOptionChoice,
    CacheType,
    Channel,
    ChatInputCommandInteraction,
    PermissionFlagsBits,
    PermissionsBitField,
    SlashCommandBuilder,
    SlashCommandSubcommandBuilder,
    SlashCommandSubcommandGroupBuilder
} from "discord.js";
import { getSetting, setSetting } from "../data/settings";

export class SettingsCommandBuilder extends SlashCommandBuilder {
    groups: SettingsGroupBuilder[] = [];
    constructor() {
        super();
        this.setName("settings")
            .setDescription("Bot settings")
            .setDMPermission(false)
            .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild);
    }

    findSettingsKeyForCommand(group: string, command: string): string | undefined {
        for (const group of this.groups) {
            for (const subcommand of group.subcommands) {
                if (subcommand.name === command) {
                    return subcommand.settingsKey;
                }
            }
        }
        return undefined;
    }

    findSettingTypeForCommand(group: string, command: string): "string" | "channel" | "toggle" | undefined {
        for (const group of this.groups) {
            for (const subcommand of group.subcommands) {
                if (subcommand.name === command) {
                    if (subcommand instanceof StringSetting || subcommand instanceof StringChoiceSetting) return "string";
                    if (subcommand instanceof ChannelSetting) return "channel";
                    if (subcommand instanceof ToggleSetting) return "toggle";
                }
            }
        }
        return undefined;
    }

    findDescriptionForCommand(group: string, command: string): string | undefined {
        for (const group of this.groups) {
            for (const subcommand of group.subcommands) {
                if (subcommand.name === command) {
                    return subcommand.description;
                }
            }
        }
        return undefined;
    }

    addSettingsGroup(x: SettingsGroupBuilder): this {
        this.addSubcommandGroup(x);
        this.groups.push(x);
        return this;
    }
}

export class SettingsGroupBuilder extends SlashCommandSubcommandGroupBuilder {
    subcommands: (StringSetting | StringChoiceSetting | ChannelSetting | ToggleSetting)[] = [];
    constructor(group: string) {
        super();
        this.setName(group).setDescription(`Manage settings for ${group}`);
    }

    addStringSetting(string: StringSetting | StringChoiceSetting): this {
        this.addSubcommand(string);
        this.subcommands.push(string);
        return this;
    }

    addChannelSetting(channel: ChannelSetting): this {
        this.addSubcommand(channel);
        this.subcommands.push(channel);
        return this;
    }

    addToggleSetting(toggle: ToggleSetting): this {
        this.addSubcommand(toggle);
        this.subcommands.push(toggle);
        return this;
    }
}

export class StringSetting extends SlashCommandSubcommandBuilder {
    settingsKey: string;
    constructor(name: string, settingsKey: string, description: string) {
        super();
        this.settingsKey = settingsKey;
        this.setName(name)
            .setDescription(description)
            .addStringOption((newValue) => newValue.setName("newvalue").setDescription(description));
    }
}
export class StringChoiceSetting extends SlashCommandSubcommandBuilder {
    settingsKey: string;
    constructor(name: string, settingsKey: string, description: string, choices: { display: string; value: string }[]) {
        super();
        this.settingsKey = settingsKey;
        let newChoices = choices.map((x) => {
            return {
                name: x.display,
                value: x.value
            };
        });
        this.setName(name)
            .setDescription(description)
            .addStringOption((newValue) =>
                newValue
                    .setName("newvalue")
                    .setDescription(description)
                    .setChoices(...newChoices)
            );
    }
}

export class ToggleSetting extends SlashCommandSubcommandBuilder {
    settingsKey: string;
    constructor(name: string, settingsKey: string, desc: string) {
        super();
        this.settingsKey = settingsKey;
        this.setName(name)
            .setDescription(desc)
            .addBooleanOption((newValue) => newValue.setName("newvalue").setDescription(desc));
    }
}

export class ChannelSetting extends SlashCommandSubcommandBuilder {
    /**
     * Add a channel setting
     * @param name The name displayed in the command description
     * @param settingsKey The settings key, with `Channel` appended to the end
     */
    settingsKey: string;
    constructor(name: string, settingsKey: string) {
        super();
        this.settingsKey = settingsKey;
        this.setName(name)
            .setDescription(`See what ${name} is set to or change it`)
            .addChannelOption((newValue) => newValue.setName("newvalue").setDescription(`Change ${name} to something different`));
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

export async function setChannel(
    channelName: string,
    key: string,
    interaction: ChatInputCommandInteraction<CacheType>,
    selfMemberId: string
) {
    if (!interaction.guild) return;
    if (!interaction.member) return;
    if (!interaction.options) return;

    const newChannel = interaction.options.getChannel("channel");
    const currentChannel = getSetting(interaction.guild.id, key, "");
    if (!newChannel) {
        if (currentChannel === "") {
            await interaction.reply({
                content: `There is no ${channelName} channel set`,
                ephemeral: true
            });
            return;
        }
        await interaction.reply({
            content: `The current ${channelName} channel is <#${currentChannel}>`,
            ephemeral: true
        });
        return;
    }
    if (!(await verifyTextableTextChannel(newChannel as Channel, interaction, selfMemberId))) {
        return;
    }
    setSetting(interaction.guild.id, key, newChannel.id);
    await interaction.reply({
        content: `The ${channelName} channel has been set to <#${newChannel.id}>`,
        ephemeral: true
    });
}
