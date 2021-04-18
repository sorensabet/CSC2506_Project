%% Read data
filename = 'Responses.csv';
data = readtable(filename, 'Format', '%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s');

%% Analyze data
real_major = str2num(cellfun(@(v)v(1),data.PleaseRateTheTrackOnTheScaleBelow_Rating_));
fake_minor = str2num(cellfun(@(v)v(1),data.PleaseRateTheTrackOnTheScaleBelow_Rating__1));
real_minor = str2num(cellfun(@(v)v(1),data.PleaseRateTheTrackOnTheScaleBelow_Rating__2));
fake_major = str2num(cellfun(@(v)v(1),data.PleaseRateTheTrackOnTheScaleBelow_Rating__3));

real_major = real_major(4:end);
fake_minor = fake_minor(4:end);
real_minor = real_minor(4:end);
fake_major = fake_major(4:end);

mean_real_maj = mean(real_major);
mean_fake_min = mean(fake_minor);
mean_real_min = mean(real_minor);
mean_fake_maj = mean(fake_major);
std_real_maj = std(real_major);
std_fake_min = std(fake_minor);
std_real_min = std(real_minor);
std_fake_maj = std(fake_major);

[p_maj2min, h_maj2min] = signrank(real_major, fake_minor);
[p_min2maj, h_min2maj] = signrank(real_minor, fake_major);

%% Print results
clc
fprintf('Real Major Likert Scale: %.4f ± %.4f\n', mean_real_maj, std_real_maj)
fprintf('Fake Minor Likert Scale: %.4f ± %.4f\n', mean_fake_min, std_fake_min)
fprintf('Real Minor Likert Scale: %.4f ± %.4f\n', mean_real_min, std_real_min)
fprintf('Fake Major Likert Scale: %.4f ± %.4f\n', mean_fake_maj, std_fake_maj)
fprintf('Wilcoxon Signed Rank Test for Major to Minor: p = %.4f, reject = %d\n', p_maj2min, h_maj2min)
fprintf('Wilcoxon Signed Rank Test for Minor to Major: p = %.4f, reject = %d\n', p_min2maj, h_min2maj)