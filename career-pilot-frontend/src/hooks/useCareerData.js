import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { careerApi } from "../services/careerApi";
import { useAuthStore } from "../features/auth/auth.store";

export function useCareerData() {
  const authUser = useAuthStore((state) => state.user);
  const user = { data: authUser, isLoading: false, error: null };
  const profile = useQuery({
    queryKey: ["profile"],
    queryFn: careerApi.getProfile,
    retry: (count, error) => error?.response?.status !== 404 && count < 1,
  });
  return { user, profile };
}

export function useProfileMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ mode, id, payload }) =>
      mode === "create"
        ? careerApi.createProfile(payload)
        : careerApi.updateProfile(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["profile"] }),
  });
}

export function useChildMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ action, profileId, resource, id, payload }) => {
      if (action === "delete") return careerApi.deleteChild(resource, id);
      if (action === "update") return careerApi.updateChild(resource, id, payload);
      return careerApi.createChild(resource, payload);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["profile"] }),
  });
}
