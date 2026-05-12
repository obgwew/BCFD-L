# FDScript

FDScript is a lightweight scripting language for Discord bots. Scripts are executed line by line; each command begins with `$` and takes arguments inside `[]` separated by `;`. Lines without a `$` prefix are sent as plain text to the channel.

---

## Syntax Rules

- Every command starts with `$`
- Arguments go inside `[]` and are separated by `;`
- Whitespace around tokens is ignored
- Lines starting with `#` or `//` are comments and are skipped
- A line with no `$` prefix is sent verbatim to the Discord channel
- An unclosed bracket causes a syntax error

---

## Commands

### var

Declares or sets a temporary in-memory variable. The variable lives only for the duration of the script execution.

Setter:
```
$var[name; value]
```

Getter (used inline inside other arguments):
```
$var[name]
```

Example:
```
$var[score; 10]
$sendMessage[Your score is $var[score]]
```

Output:
```
Your score is 10
```

---

### setVar / getVar

Stores and retrieves persistent variables saved to `data` on exe. These values survive across script executions.

```
$setVar[name; value]
$getVar[name]
```

`$getVar` is used inline inside arguments, not as a standalone command.

Example:
```
$setVar[visits; 42]
$sendMessage[Total visits: $getVar[visits]]
```

Output:
```
Total visits: 42
```

---

### sendMessage

Sends a text message to the current channel.

```
$sendMessage[text]
```

Example:
```
$sendMessage[Hello from the bot!]
```

Output:
```
Hello from the bot!
```

---

### embed

Sends a Discord embed with a title, description, and hex color.

```
$embed[title; description; hexColor]
```

Example:
```
$embed[Welcome; Thanks for joining the server.; 2ecc71]
```

Output: A Discord embed card with the title "Welcome", the given description, and a green sidebar color.

---

## Built-in Variables

Read-only references resolved at runtime. Use them inline anywhere with `$name`.

| Variable     | Value                                          |
|--------------|------------------------------------------------|
| $authorID    | Numeric ID of the message author               |
| $authorName  | Username of the message author                 |
| $mention     | Mention string of the message author           |
| $channelID   | Numeric ID of the current channel              |
| $channelName | Name of the current channel                    |
| $guildName   | Name of the current server                     |
| $message     | Full content of the triggering message         |
| $botName     | Username of the bot                            |
| $botID       | Numeric ID of the bot                          |

Example:
```
$sendMessage[Hello $authorName, your ID is $authorID]
```

Output:
```
Hello user, your ID is 123456789012345678
```

---

## Math Commands

Each command takes exactly two numeric arguments and sends the result to the channel. All four can also be used inline inside other arguments.

```
$sum[a; b]
$sub[a; b]
$mul[a; b]
$div[a; b]
```

Division by zero produces an error message instead of crashing.

Example:
```
$var[x; 8]
$var[y; 3]
$sum[$var[x]; $var[y]]
$sub[$var[x]; $var[y]]
$mul[$var[x]; $var[y]]
$div[$var[x]; $var[y]]
```

Output:
```
11
5
24
2.666
```

Inline usage:
```
$var[x; 8]
$sendMessage[Result is $sum[$var[x]; 2]]
```

Output:
```
Result is 10
```

---

## if / elif / else / endif

Evaluates a condition and executes the matching branch. Supported operators: `==` `!=` `>` `<` `>=` `<=`. Numeric strings are compared numerically; non-numeric strings fall back to lexicographic comparison.

```
$if[condition]
  ...
$elif[condition]
  ...
$else
  ...
$endif
```

Example:
```
$var[score; 75]
$if[$var[score] >= 90]
$sendMessage[Grade: A]
$elif[$var[score] >= 60]
$sendMessage[Grade: B]
$else
$sendMessage[Grade: F]
$endif
```

Output:
```
Grade: B
```

---

## while / endwhile

Repeats a block as long as a condition is true.

```
$while[condition]
  ...
$endwhile
```

Example:
```
$var[n; 1]
$while[$var[n] <= 3]
$sendMessage[Iteration $var[n]]
$var[n; $sum[$var[n]; 1]]
$endwhile
```

Output:
```
Iteration 1
Iteration 2
Iteration 3
```

---

## for / endfor

Repeats a block a fixed number of times. The count must resolve to a whole number.

```
$for[count]
  ...
$endfor
```

Example:
```
$for[3]
$sendMessage[Hello!]
$endfor
```

Output:
```
Hello!
Hello!
Hello!
```

---

## break

Exits the nearest enclosing `$while` or `$for` loop immediately.

```
$break (It's still experimental and has problems.)
```

Example:
```
$var[n; 0]
$while[$var[n] < 10]
$var[n; $sum[$var[n]; 1]]
$if[$var[n] == 4]
$break
$endif
$endwhile
$sendMessage[Stopped at $var[n]]
```

Output:
```
Stopped at 4
```

---

## strictArgs

Checks that the user provided an argument after the command trigger. If the message has no text beyond the command name, the error message is sent and execution continues past it.

```
$strictArgs[$message==; error text]
```

Example:
```
$strictArgs[$message==; Please provide a username.]
$sendMessage[Looking up: $message]
```

When the user sends the command with no argument:
```
Please provide a username.
```

When the user sends the command followed by a name:
```
Looking up: user
```

---

## Plain Text

Any line that does not start with `$` is sent directly to the channel. Built-in variables are resolved before sending.

Example:
```
Welcome to the server, $authorName!
Your channel is #$channelName.
```

Output:
```
Welcome to the server, user!
Your channel is #general.
```

---

## Error Handling

FDScript validates all commands before execution begins. If any error is found, execution stops and the error is reported to the channel. No partial execution occurs.

| Error                  | Cause                                                       |
|------------------------|-------------------------------------------------------------|
| Unknown command        | A `$name` that is not in the recognized command list        |
| Syntax error           | An unclosed `[` bracket                                     |
| Wrong argument count   | Passing the wrong number of arguments to a command          |
| Non-numeric argument   | Passing a string where a number is expected                 |
| Division by zero       | Second argument to `$div` resolves to `0`                   |

Example:
```
$wew[now]
```

Output:
```
Unknown command: wew
```

---

## Full Examples

### Persistent hit counter

```
$var[count; $getVar[hits]]
$var[count; $sum[$var[count]; 1]]
$setVar[hits; $var[count]]
$sendMessage[$authorName, you have used this command $var[count] times.]
```

Output on the third call:
```
user, you have used this command 3 times.
```

### Simple guessing game

```
$strictArgs[$message; Please provide a number.]
$var[guess; $message]
$var[answer; 7]
$if[$var[guess] == $var[answer]]
$sendMessage[Correct!]
$else
$sendMessage[Wrong, try again.]
$endif
```

### Embed announcement

```
$embed[title; Description; hex-color]
```

Output: A Discord embed with an orange color and the given title and description.

---

## Variable Resolution Order

When `$var[name]` is encountered, the interpreter resolves it in this order:

1. Temporary in-memory variables set with `$var[name; value]`
2. Built-in read-only variables such as `$authorID` and `$channelName`

Persistent variables set with `$setVar` are accessed only via `$getVar[name]` and are not part of the above lookup chain.