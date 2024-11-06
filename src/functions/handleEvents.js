import chalk from "chalk";

export default (client) => {
  client.handleEvents = async (eventFiles, path) => {
    for (const file of eventFiles) {
      const event = await import(`../events/${file}`);

      const eventHandler = event.default || event;

      if (eventHandler.once) {
        client.once(eventHandler.name, (...args) => {
          try {
            eventHandler.execute(...args, client);
          } catch (error) {
            console.log(
              `Error while executing the ${eventHandler.name} event: `,
              error,
            );
          }
        });
      } else {
        client.on(eventHandler.name, (...args) => {
          eventHandler.execute(...args, client);
        });
      }
    }
  };
};
