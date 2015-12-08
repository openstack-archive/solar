function make_arr(data)
   local t = {}
   for orig_value in python.iter(data) do
      if t[orig_value["resource"]] == nil then
         t[orig_value["resource"]] = {}
      end
      t[orig_value["resource"]][orig_value['other_input']] = orig_value['value']
   end
   return t
end
