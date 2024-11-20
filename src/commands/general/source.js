/*
 * DISCLAIMER:
 *
 * The source code of this project is licensed under the GNU General Public License (GPL) v3.
 *
 * IMPORTANT NOTICE REGARDING THE "source" COMMAND:
 *
 * The "source" command or functionality is an integral part of this software and MUST NOT
 * be removed, altered, or disabled in any way. This command provides users with access to
 * important project information, including the original source code and licensing details.
 *
 * The "source" command is defined as the function or method that allows users to access
 * the original source code, documentation, or the terms of the GNU General Public License
 * under which this project is distributed. It must remain in the source code, in its original
 * form, and be fully operational in any redistribution or modification of the code.
 *
 * Removing or disabling the "source" command constitutes a violation of the terms of this license.
 * You are NOT permitted to remove, modify, or otherwise tamper with this command.
 *
 * If you are redistributing or modifying this code, you must ensure that the "source" command
 * remains intact and fully functional. Failure to comply with this requirement may result in legal
 * action under the terms of the GPL v3 license.
 *
 * This software is provided "as is" without any warranty, express or implied, under the terms of
 * the GPL v3. For more information, please refer to the full GNU General Public License.
 *
 * You should have received a copy of the GNU General Public License along with this program.
 * If not, see <https://www.gnu.org/licenses/>.
 *
 * END OF DISCLAIMER.
 */

import { SlashCommandBuilder } from "discord.js";

const data = new SlashCommandBuilder()
  .setName("source")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2)
  .setDescription("Get the source information for this project");

const execute = async function (interaction) {
  await interaction.reply({
    embeds: [
      {
        title: "Source Information",
        fields: [
          {
            name: "Author",
            value: "Cyteon - https://github.com/cyteon",
          },
          {
            name: "📜 License",
            value: "GNU Affero General Public License v3 + extra terms",
          },
          {
            name: "📜 GNU AGPL v3",
            value: "https://www.gnu.org/licenses/agpl-3.0.html",
          },
          {
            name: "📜 Extra Terms",
            value: `\`\`\`
In addition to the terms of the GNU Affero General Public License, the following restriction applies:

1. The "source" command or functionality must always be included in the source code. This command or functionality must not be removed, altered, or disabled in any way.
   The "source" command is defined as the function or method that provides access to the originalsource code or other relevant project information.
                        \`\`\``,
          },
        ],
      },
    ],
    components: [
      {
        type: 1,
        components: [
          {
            type: 2,
            style: 5,
            emoji: "📁",
            label: "View Source",
            url: "https://github.com/cyteon/potatobot",
          },
          {
            type: 2,
            style: 5,
            emoji: "📜",
            label: "View License",
            url: "https://raw.githubusercontent.com/Cyteon/potatobot/refs/heads/v3-js/LICENSE",
          },
        ],
      },
    ],
  });
};

export default { data, execute };
