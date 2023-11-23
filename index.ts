import { Client, ClientOptions, REST, Routes } from "discord.js";
import { AllCommands, Module } from "./modules/type";
import { Suggestions } from "./modules/suggestions";
import * as dotenv from "dotenv";

dotenv.config();

if (!process.env.TOKEN) {
  throw new Error("No token provided");
}

const options: ClientOptions = {
  intents: ["Guilds", "GuildMessages", "GuildMembers"],
};

const client = new Client(options);
const restClient = new REST({ version: "9" }).setToken(process.env.TOKEN);
const modules: Module[] = [];

modules.push(new Suggestions());

client.on("ready", () => {
  console.log("I am ready!");
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

client.login(process.env.TOKEN);
