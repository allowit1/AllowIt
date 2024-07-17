using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

class Program
{
    static void AddPartner(string baseDirectory, string group, string partner, string accessType)
    {
        string groupFilePath = Path.Combine(baseDirectory, "groups", "TestOfAutomation.yml");
        string repoFilePath = Path.Combine(baseDirectory, "repos", "Example_Repo.yml");
        
        var groupData = ReadYaml(groupFilePath);
        var repoData = ReadRepoYaml(repoFilePath);
        
        string fullGroupName = $"{group}_{accessType}";

        // Update group file
        UpdateGroupFile(groupData, fullGroupName, partner);

        // Remove from other access types in group file
        RemoveFromOtherAccessTypes(groupData, group, partner, accessType);

        // Update repo file
        UpdateRepoFile(repoData, group, accessType);

        WriteYaml(groupFilePath, groupData);
        WriteRepoYaml(repoFilePath, repoData);
        Console.WriteLine($"Partner {partner} added to {fullGroupName}");
    }

    static void UpdateGroupFile(Dictionary<string, List<string>> groupData, string fullGroupName, string partner)
    {
        if (!groupData.ContainsKey(fullGroupName))
        {
            groupData[fullGroupName] = new List<string>();
        }
        if (!groupData[fullGroupName].Contains(partner))
        {
            groupData[fullGroupName].Add(partner);
        }
    }

    static void RemoveFromOtherAccessTypes(Dictionary<string, List<string>> groupData, string group, string partner, string currentAccessType)
    {
        string[] allAccessTypes = { "read", "triage", "write" };
        foreach (var accessType in allAccessTypes)
        {
            if (accessType != currentAccessType)
            {
                string groupName = $"{group}_{accessType}";
                if (groupData.ContainsKey(groupName))
                {
                    groupData[groupName].Remove(partner);
                    if (groupData[groupName].Count == 0)
                    {
                        groupData.Remove(groupName);
                    }
                }
            }
        }
    }

    static void UpdateRepoFile(Dictionary<string, Dictionary<string, object>> repoData, string group, string accessType)
    {
        string fullGroupName = $"{group}_{accessType}";
        if (!repoData.ContainsKey("Example_Repo"))
        {
            repoData["Example_Repo"] = new Dictionary<string, object>();
        }
        
        var repoGroup = repoData["Example_Repo"];
        repoGroup[fullGroupName] = new Dictionary<string, object>
        {
            { "type", "group" },
            { "permissions", accessType }
        };
    }

    static void RemovePartner(string baseDirectory, string group, string partner, string accessType)
    {
        string groupFilePath = Path.Combine(baseDirectory, "groups", "TestOfAutomation.yml");
        string repoFilePath = Path.Combine(baseDirectory, "repos", "Example_Repo.yml");
        
        var groupData = ReadYaml(groupFilePath);
        var repoData = ReadRepoYaml(repoFilePath);
        
        string fullGroupName = $"{group}_{accessType}";

        if (groupData.ContainsKey(fullGroupName))
        {
            if (groupData[fullGroupName].Remove(partner))
            {
                if (groupData[fullGroupName].Count == 0)
                {
                    groupData.Remove(fullGroupName);
                    // Also remove from repo file if group is empty
                    if (repoData.ContainsKey("Example_Repo"))
                    {
                        ((Dictionary<string, object>)repoData["Example_Repo"]).Remove(fullGroupName);
                    }
                }
                WriteYaml(groupFilePath, groupData);
                WriteRepoYaml(repoFilePath, repoData);
                Console.WriteLine($"Partner {partner} removed from {fullGroupName}");
            }
            else
            {
                Console.WriteLine($"Partner {partner} not found in {fullGroupName}");
            }
        }
        else
        {
            Console.WriteLine($"Group {fullGroupName} not found");
        }
    }

    static Dictionary<string, List<string>> ReadYaml(string filePath)
    {
        if (!File.Exists(filePath))
        {
            return new Dictionary<string, List<string>>();
        }

        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(CamelCaseNamingConvention.Instance)
            .Build();

        using (var reader = new StreamReader(filePath))
        {
            return deserializer.Deserialize<Dictionary<string, List<string>>>(reader);
        }
    }

    static Dictionary<string, Dictionary<string, object>> ReadRepoYaml(string filePath)
    {
        if (!File.Exists(filePath))
        {
            return new Dictionary<string, Dictionary<string, object>>();
        }

        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(CamelCaseNamingConvention.Instance)
            .Build();

        using (var reader = new StreamReader(filePath))
        {
            return deserializer.Deserialize<Dictionary<string, Dictionary<string, object>>>(reader);
        }
    }

    static void WriteYaml(string filePath, Dictionary<string, List<string>> data)
    {
        var serializer = new SerializerBuilder()
            .WithNamingConvention(CamelCaseNamingConvention.Instance)
            .Build();

        var yaml = serializer.Serialize(data);
        File.WriteAllText(filePath, yaml.Trim());
    }

    static void WriteRepoYaml(string filePath, Dictionary<string, Dictionary<string, object>> data)
    {
        var serializer = new SerializerBuilder()
            .WithNamingConvention(CamelCaseNamingConvention.Instance)
            .Build();

        var yaml = serializer.Serialize(data);
        File.WriteAllText(filePath, yaml.Trim());
    }

    static void RunGitCommand(string baseDirectory, string arguments)
    {
        var processStartInfo = new ProcessStartInfo
        {
            FileName = "git",
            Arguments = arguments,
            WorkingDirectory = baseDirectory,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        using (var process = new Process { StartInfo = processStartInfo })
        {
            process.Start();
            string output = process.StandardOutput.ReadToEnd();
            string error = process.StandardError.ReadToEnd();
            process.WaitForExit();

            if (process.ExitCode != 0)
            {
                throw new Exception($"Git command failed with error: {error}");
            }
        }
    }

    static void PushToGitHub(string baseDirectory, string commitMessage)
    {
        try
        {
            RunGitCommand(baseDirectory, "add .");
            RunGitCommand(baseDirectory, $"commit -m \"{commitMessage}\"");
            RunGitCommand(baseDirectory, "push");
            Console.WriteLine("Changes pushed to GitHub successfully.");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"An error occurred while pushing to GitHub: {ex.Message}");
        }
    }

    static void Main(string[] args)
    {
        string baseDirectory = @"C:\Users\User\Documents\Automation_Test\AllowIt";

        // AddPartner(baseDirectory, "example_group1", "benayat1", "write");
        // RemovePartner(baseDirectory, "example_group1", "maor-noy", "write");
        // AddPartner(baseDirectory, "example_group1", "partner3", "triage");
        // AddPartner(baseDirectory, "example_group1", "partner2", "read");
        // RemovePartner(baseDirectory, "example_group1", "partner3", "triage");

        //AddPartner(baseDirectory, "example_group1", "maornoy1310@gmail.com", "write");
        //AddPartner(baseDirectory, "example_group1", "yeretyn@gmail.com", "write");
        //AddPartner(baseDirectory, "example_group1", "manoy@g.jct.ac.il", "write");
        //AddPartner(baseDirectory, "example_group1", "YairLevi03", "write");
        //RemovePartner(baseDirectory, "example_group1", "benayat1", "write");

        PushToGitHub(baseDirectory, "Your commit message here");
    }
}
