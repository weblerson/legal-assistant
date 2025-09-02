import { Client } from "whatsapp-web.js";
import axios from "axios"; 

const client = new Client();

client.on("qr", (qr) => {
  console.log("QR Code", qr);
});

client.on("ready", () => {
  console.log("Client is ready!");
});

client.on("message", async (msg) => {
  const userQuery = msg.body
  const response = await axios.post("http://localhost:5000/query/", {
    query: userQuery,
  })

  const modelResponse = response.data.response
  msg.reply(modelResponse)

  // if (msg.body == "!ping") {
  //   msg.reply("pong");
  // }
});

client.initialize();
