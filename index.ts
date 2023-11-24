import { Client, ClientOptions, REST, Routes } from "discord.js";
import { AllCommands, Module } from "./modules/type";
import { Suggestions } from "./modules/suggestions";
import * as dotenv from "dotenv";
import { Logging } from "./modules/logging";
import { SettingsModule } from "./modules/settings";
import { LevelingModule } from "./modules/leveling";

dotenv.config();

if (!process.env.TOKEN) {
  throw new Error("No token provided");
}

const options: ClientOptions = {
  intents: [
    "Guilds",
    "GuildMessages",
    "GuildMembers",
    "MessageContent",
    "GuildBans",
    "GuildModeration",
  ],
};

const client = new Client(options);
const restClient = new REST({ version: "9" }).setToken(process.env.TOKEN);
const modules: Module[] = [];

modules.push(new Suggestions());
modules.push(new Logging());
modules.push(new SettingsModule());
modules.push(new LevelingModule());

client.on("ready", () => {
  console.log("I am ready!");
  modules.forEach((module) => {
    module.selfMemberId = client.user?.id || "";
  });
  try {
    let commands: AllCommands = [];
    modules.forEach((module) => {
      commands = [...commands, ...module.commands];
    });
    restClient.put(
      Routes.applicationGuildCommands(
        "1172922944033411243",
        "1144262375281799179"
      ),
      {
        body: commands,
      }
    );
  } catch (error) {
    console.error(error);
  }
});

client.on("messageCreate", async (message) => {
  if (!message.guild) return;

  modules.forEach(async (module) => {
    await module.onMessage(message);
  });
});

client.on("interactionCreate", async (interaction) => {
  if (interaction.isButton()) {
    modules.forEach(async (module) => {
      await module.onButtonClick(interaction);
    });
  }

  if (interaction.isChatInputCommand()) {
    modules.forEach(async (module) => {
      await module.onSlashCommand(interaction);
    });
  }
});

client.on("guildMemberAdd", async (member) => {
  modules.forEach(async (module) => {
    await module.onMemberJoin(member);
  });
});

client.on("guildMemberRemove", async (member) => {
  modules.forEach(async (module) => {
    await module.onMemberLeave(member);
  });
});

client.on("guildMemberUpdate", async (before, after) => {
  modules.forEach(async (module) => {
    await module.onMemberEdit(before, after);
  });
});

client.on("messageDelete", async (message) => {
  modules.forEach(async (module) => {
    await module.onMessageDelete(message);
  });
});

client.on("messageUpdate", async (before, after) => {
  modules.forEach(async (module) => {
    await module.onMessageEdit(before, after);
  });
});

client.on("channelCreate", async (channel) => {
  modules.forEach(async (module) => {
    await module.onChannelCreate(channel);
  });
});

client.on("channelDelete", async (channel) => {
  modules.forEach(async (module) => {
    await module.onChannelDelete(channel);
  });
});

client.on("channelUpdate", async (before, after) => {
  modules.forEach(async (module) => {
    await module.onChannelEdit(before, after);
  });
});

client.on("roleCreate", async (role) => {
  modules.forEach(async (module) => {
    await module.onRoleCreate(role);
  });
});

client.on("roleDelete", async (role) => {
  modules.forEach(async (module) => {
    await module.onRoleDelete(role);
  });
});

client.on("roleUpdate", async (before, after) => {
  modules.forEach(async (module) => {
    await module.onRoleEdit(before, after);
  });
});

client.on("error", (error) => {
  console.error(error);
});

client.login(process.env.TOKEN);
