# FDScript.py

import discord
import asyncio

class ExecutionContext:
    def __init__(self, message, bot):
        self.message = message
        self.bot = bot
        self.vars = {
            "$authorID": str(message.author.id),
            "$authorName": message.author.name,
            "$channelID": str(message.channel.id),
            "$channelName": message.channel.name,
            "$guildName": message.guild.name if message.guild else "DM",
            "$mention": message.author.mention,
            "$botName": bot.user.name if bot.user else "",
            "$botID": str(bot.user.id) if bot.user else "",
            "$messageContent": message.content
        }
        self._run_block = True

    def substitute_vars(self, text):
        for key, val in self.vars.items():
            text = text.replace(f"${key}", str(val))
        return text

class CustomInterpreter:
    def __init__(self, script):
        self.lines = [
            line.strip()
            for line in script.splitlines()
            if line.strip() and not line.strip().startswith(("#", "//"))
        ]

    async def run(self, ctx):
        i = 0
        while i < len(self.lines):
            line = self.lines[i]

            if not ctx._run_block and not line.startswith(("$endif", "$endloop")):
                i += 1
                continue

            if line.startswith(("$set[", "$setVar[")):
                expr = self._extract(line, "$set" if "$set[" in line else "$setVar")
                key, val = map(str.strip, expr.split("=", 1))
                ctx.vars[key] = ctx.substitute_vars(val)

            elif line.startswith("$sendMessage["):
                text = ctx.substitute_vars(self._extract(line, "$sendMessage"))
                await ctx.message.channel.send(text)

            elif line.startswith("$reply["):
                text = ctx.substitute_vars(self._extract(line, "$reply"))
                await ctx.message.reply(text)

            elif line.startswith("$sendDM["):
                text = ctx.substitute_vars(self._extract(line, "$sendDM"))
                await ctx.message.author.send(text)

            elif line.startswith("$mention["):
                text = ctx.substitute_vars(self._extract(line, "$mention"))
                await ctx.message.channel.send(f"{ctx.message.author.mention} {text}")

            elif line.startswith("$embed["):
                content = self._extract(line, "$embed")
                title, desc = map(str.strip, content.split("|", 1))
                embed = discord.Embed(
                    title=ctx.substitute_vars(title),
                    description=ctx.substitute_vars(desc),
                    color=0x00FF00
                )
                await ctx.message.channel.send(embed=embed)

            elif line.startswith("$log["):
                print("$LOG:", ctx.substitute_vars(self._extract(line, "$log")))

            elif line.startswith("$wait["):
                seconds = float(self._extract(line, "$wait"))
                await asyncio.sleep(seconds)

            elif line.startswith("$if["):
                cond = self._extract(line, "$if")
                ctx._run_block = self._evaluate(cond, ctx)

            elif line == "$else":
                ctx._run_block = not ctx._run_block

            elif line == "$endif":
                ctx._run_block = True

            elif line.startswith("$loop["):
                count = int(self._extract(line, "$loop"))
                block = []
                i += 1
                while i < len(self.lines) and self.lines[i] != "$endloop":
                    block.append(self.lines[i])
                    i += 1
                i += 1
                for _ in range(count):
                    for sub in block:
                        await self.run_line(sub, ctx)
                continue

            else:
                await self.run_line(line, ctx)

            i += 1

    async def run_line(self, line, ctx):
        if line.startswith("$sendMessage["):
            text = ctx.substitute_vars(self._extract(line, "$sendMessage"))
            await ctx.message.channel.send(text)
        elif line.startswith("$reply["):
            text = ctx.substitute_vars(self._extract(line, "$reply"))
            await ctx.message.reply(text)
        elif line.startswith("$sendDM["):
            text = ctx.substitute_vars(self._extract(line, "$sendDM"))
            await ctx.message.author.send(text)
        elif line.startswith("$mention["):
            text = ctx.substitute_vars(self._extract(line, "$mention"))
            await ctx.message.channel.send(f"{ctx.message.author.mention} {text}")

    def _extract(self, line, cmd):
        prefix = f"{cmd}["
        if not (line.startswith(prefix) and line.endswith("]")):
            raise ValueError(f"Invalid syntax for {cmd}: {line}")
        return line[len(prefix):-1]

    def _evaluate(self, expr, ctx):
        expr = ctx.substitute_vars(expr)
        if "==" in expr:
            left, right = map(str.strip, expr.split("==", 1))
            for conv in (int, float):
                try:
                    left, right = conv(left), conv(right)
                    break
                except:
                    pass
            return left == right
        return False

async def run_script(message, bot, script_text):
    ctx = ExecutionContext(message, bot)
    interpreter = CustomInterpreter(script_text)
    await interpreter.run(ctx)
    