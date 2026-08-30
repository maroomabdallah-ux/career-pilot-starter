import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { careerApi } from "../services/careerApi";
import useAppStore from "../store/useAppStore";

export function useCareerData() {
  const userId = useAppStore((state) => state.userId);
  const user = useQuery({
    queryKey: ["user", userId],
    queryFn: () => careerApi.getUser(userId),
    enabled: Boolean(userId),
  });
  const profile = useQuery({
    queryKey: ["profile", userId],
    queryFn: () => careerApi.getProfileByUser(userId),
    enabled: Boolean(userId),
    retry: (count, error) => error?.response?.status !== 404 && count < 1,
  });
  return { userId, user, profile };
}

export function useProfileMutation() {
  const queryClient = useQueryClient();
  const userId = useAppStore((state) => state.userId);
  return useMutation({
    mutationFn: ({ mode, id, payload }) =>
      mode === "create"
        ? careerApi.createProfile({ ...payload, user_id: userId })
        : careerApi.updateProfile(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["profile", userId] }),
  });
}

export function useChildMutation() {
  const queryClient = useQueryClient();
  const userId = useAppStore((state) => state.userId);
  return useMutation({
    mutationFn: ({ action, profileId, resource, id, payload }) => {
      if (action === "delete") return careerApi.deleteChild(resource, id);
      if (action === "update") return careerApi.updateChild(resource, id, payload);
      return careerApi.createChild(profileId, resource, payload);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["profile", userId] }),
  });
}
