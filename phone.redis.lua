local phone_no=ARGV[1]
local isTrial=(string.upper(ARGV[2]) == 'TRUE')
local org_id=ARGV[3]

local generic_rules=KEYS[1] 
local trial_rules=KEYS[2]
local org_rules=KEYS[3]

redis.log(redis.LOG_NOTICE, 
    'called with keys:', generic_rules, trial_rules, org_rules, 
    'and arguments:', phone_no, isTrial, org_id
)

local rule_allows = function(rule) 
    return rule == 'allow'
end
local rule_restricts = function(rule) 
    return rule == 'restrict'
end

local get_rule = function(key, prefix)
    --[[--
    -- Look up a specific rule in redis 
    --
    -- Will also log a debug message if a rule is found.
    -- Any value other than the 'allow' and 'restrict' keywords is ignored with  
    -- a warning log.
    --
    -- @Parameter: key
    --    The key of a redis hash
    -- @Parameter: prefix 
    --    The key in the redus has denoted by key
    -- @Returns: 
    --    'alow' or 'restrict' if there is a specific rule at key and prefix or nil otherwhise
    --]]--
    local prefix_rule = redis.call('HGET', key, prefix)
    redis.log(redis.LOG_NOTICE, 'inspecting', key, prefix)
    if prefix_rule  then
        -- TODO make DEBUG
        redis.log(redis.LOG_NOTICE, 
            'Found rule for key:', key, 'prefix:', prefix, ' policy is', string.upper(prefix_rule)
        )
        if rule_allows(prefix_rule) or rule_restricts(prefix_rule) then
            return prefix_rule
        else 
            redis.log(redis.LOG_WARNING, 
                'Invalid keyword for rule key:', key, 'prefix:', prefix, ' was ', prefix_rule,
                'but expected one of "allow" or "restrict"'
            ) 
            return nil
        end
    end
    return nil
end

local check_and_warn_org_restrictions = function(rule, org_id)
    --[[--
    -- Check if the rule belonging to an organization is restrictive and issue a warning 
    --
    -- @Parameter: rule 
    --   An organization specific rule
    -- @Parameter: org_id
    --   The organisation Id the rule belongs to
    -- @Returns: true if the rule is a restriction
    --]]--
    if rule_restricts(rule) then 
        redis.log(redis.LOG_WARNING, 
         'Found a restrictive rule for organisation with id: ', org_id, 
         'Restrictions might apply for organisation only'
        )
        return true
    end
    return false
end

local check_and_warn_trial_restrictions = function(rule, prefix)
    --[[--
    -- Check if the trial specific rule is permissive and issue a warning
    -- @Parameter: rule 
    --   A trial specific rule 
    -- @Parameter: prefix
    --   The prefix the rule applies to
    -- @Returns: true if  the rule is a permissive one 
    --]]--
    if rule_allows(rule) then
        redis.log(redis.LOG_WARNING, 
         'Found a permissive trial rule for prefix: ', prefix,
         'Might allow some calls only in trial.'
        )
        return true
    end
    return false
end

-- Org specific rules are expected in < 2% of users, thus the special 'enable' keys 
-- to skip going trough all prefixes for org specific most of the time
local org_specific=false
if org_id then
    if org_id then
        if redis.call('HGET', org_rules, org_id) == 'enable' then
            redis.log(redis.LOG_NOTICE, 
                'Org specific rules are enabled for', org_id
            )
            org_specific=true
        end  
    end
end

-- check all org specific first, 
-- organisation might alow whole "12" prefix, but generic rules restrict "123"
if org_specific == true then 
    -- generate all prefixes starting from most specific 
    -- (the phone number itself) to least specific ( the first digit)
    for i=string.len(phone_no), 1, -1 do 
       local prefix = string.sub(phone_no, 1, i)
       local prefix_rule = get_rule(org_rules, org_id .. ':' .. prefix)
       check_and_warn_org_restrictions(prefix_rule, org_id)
       if prefix_rule ~= nil then return prefix_rule end
    end
end
    
for i=string.len(phone_no), 1, -1 do 
    local prefix_rule = get_rule(generic_rules, prefix)
    if prefix_rule ~= nil then return prefix_rule end
    
    if isTrial == true then
       local prefix_rule = get_rule(trial_rules, prefix)
       check_and_warn_trial_restrictions(prefix_rule, prefix)
       if prefix_rule ~= nil then return prefix_rule end
   end
end
-- allow the caller to implement default behavior if no rules
return nil
